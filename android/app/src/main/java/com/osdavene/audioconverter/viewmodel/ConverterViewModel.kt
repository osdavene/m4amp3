package com.osdavene.audioconverter.viewmodel

import android.app.Application
import android.net.Uri
import android.provider.OpenableColumns
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.osdavene.audioconverter.model.AudioFileItem
import com.osdavene.audioconverter.model.ConversionStatus
import com.osdavene.audioconverter.service.AudioConverterEngine
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ConverterViewModel(application: Application) : AndroidViewModel(application) {

    private val _selectedFiles = MutableStateFlow<List<AudioFileItem>>(emptyList())
    val selectedFiles: StateFlow<List<AudioFileItem>> = _selectedFiles.asStateFlow()

    private val _targetFormat = MutableStateFlow("mp3")
    val targetFormat: StateFlow<String> = _targetFormat.asStateFlow()

    private val _targetBitrate = MutableStateFlow("192k")
    val targetBitrate: StateFlow<String> = _targetBitrate.asStateFlow()

    private val _isConverting = MutableStateFlow(false)
    val isConverting: StateFlow<Boolean> = _isConverting.asStateFlow()

    private val _globalProgress = MutableStateFlow(0f)
    val globalProgress: StateFlow<Float> = _globalProgress.asStateFlow()

    private val _statusMessage = MutableStateFlow("Listo para seleccionar archivos")
    val statusMessage: StateFlow<String> = _statusMessage.asStateFlow()

    private var conversionJob: Job? = null

    fun setTargetFormat(format: String) {
        _targetFormat.value = format
    }

    fun setTargetBitrate(bitrate: String) {
        _targetBitrate.value = bitrate
    }

    fun addUris(uris: List<Uri>) {
        val context = getApplication<Application>().applicationContext
        val newItems = mutableListOf<AudioFileItem>()

        for (uri in uris) {
            var displayName = "audio_${System.currentTimeMillis()}"
            var sizeBytes = 0L

            try {
                context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                    val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
                    if (cursor.moveToFirst()) {
                        if (nameIndex != -1) displayName = cursor.getString(nameIndex) ?: displayName
                        if (sizeIndex != -1) sizeBytes = cursor.getLong(sizeIndex)
                    }
                }
            } catch (_: Exception) {}

            val ext = displayName.substringAfterLast(".", "").lowercase()
            
            // Evitar duplicados por URI
            if (_selectedFiles.value.none { it.uri == uri }) {
                newItems.add(
                    AudioFileItem(
                        uri = uri,
                        name = displayName,
                        sizeBytes = sizeBytes,
                        extension = ext
                    )
                )
            }
        }

        if (newItems.isNotEmpty()) {
            _selectedFiles.value = _selectedFiles.value + newItems
            _statusMessage.value = "${_selectedFiles.value.size} archivo(s) listos para convertir"
        }
    }

    fun removeFile(item: AudioFileItem) {
        if (_isConverting.value) return
        _selectedFiles.value = _selectedFiles.value.filter { it.id != item.id }
        _statusMessage.value = if (_selectedFiles.value.isEmpty()) {
            "Listo para seleccionar archivos"
        } else {
            "${_selectedFiles.value.size} archivo(s) seleccionados"
        }
    }

    fun clearAll() {
        if (_isConverting.value) return
        _selectedFiles.value = emptyList()
        _globalProgress.value = 0f
        _statusMessage.value = "Listo para seleccionar archivos"
    }

    fun startConversion() {
        if (_isConverting.value || _selectedFiles.value.isEmpty()) return

        _isConverting.value = true
        _globalProgress.value = 0f
        val totalFiles = _selectedFiles.value.size
        val format = _targetFormat.value
        val bitrate = _targetBitrate.value
        val context = getApplication<Application>().applicationContext

        conversionJob = viewModelScope.launch {
            var successCount = 0

            for ((index, item) in _selectedFiles.value.withIndex()) {
                // Actualizar estado del item a CONVERTING
                updateItemStatus(item.id, ConversionStatus.CONVERTING, 0.2f)
                _statusMessage.value = "Convirtiendo (${index + 1}/$totalFiles): ${item.name}"

                val result = AudioConverterEngine.convertAudio(
                    context = context,
                    inputUri = item.uri,
                    inputName = item.name,
                    targetFormat = format,
                    bitrate = bitrate,
                    onProgress = { p ->
                        updateItemStatus(item.id, ConversionStatus.CONVERTING, p)
                    }
                )

                if (result.isSuccess) {
                    successCount++
                    updateItemStatus(
                        id = item.id,
                        status = ConversionStatus.SUCCESS,
                        progress = 1.0f,
                        outputPath = result.getOrNull()
                    )
                } else {
                    updateItemStatus(
                        id = item.id,
                        status = ConversionStatus.ERROR,
                        progress = 0f,
                        error = result.exceptionOrNull()?.message ?: "Error desconocido"
                    )
                }

                _globalProgress.value = (index + 1).toFloat() / totalFiles.toFloat()
            }

            _isConverting.value = false
            _statusMessage.value = "✅ ¡Listo! $successCount/$totalFiles convertidos en Música/ConvertedAudio"
        }
    }

    fun cancelConversion() {
        conversionJob?.cancel()
        _isConverting.value = false
        _statusMessage.value = "Conversión cancelada"
    }

    private fun updateItemStatus(
        id: String,
        status: ConversionStatus,
        progress: Float,
        outputPath: String? = null,
        error: String? = null
    ) {
        _selectedFiles.value = _selectedFiles.value.map { item ->
            if (item.id == id) {
                item.copy(
                    status = status,
                    progress = progress,
                    outputPath = outputPath ?: item.outputPath,
                    errorMessage = error
                )
            } else {
                item
            }
        }
    }
}
