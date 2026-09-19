package com.osdavene.audioconverter.service

import android.content.ContentValues
import android.content.Context
import android.media.MediaScannerConnection
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import com.arthenica.ffmpegkit.FFmpegKit
import com.arthenica.ffmpegkit.FFmpegKitConfig
import com.arthenica.ffmpegkit.ReturnCode
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

object AudioConverterEngine {

    private val CODEC_MAP = mapOf(
        "mp3" to listOf("-c:a", "libmp3lame"),
        "m4a" to listOf("-c:a", "aac"),
        "aac" to listOf("-c:a", "aac"),
        "wav" to listOf("-c:a", "pcm_s16le"),
        "flac" to listOf("-c:a", "flac"),
        "ogg" to listOf("-c:a", "libvorbis"),
        "opus" to listOf("-c:a", "libopus"),
        "wma" to listOf("-c:a", "wmav2"),
        "aiff" to listOf("-c:a", "pcm_s16be")
    )

    suspend fun convertAudio(
        context: Context,
        inputUri: Uri,
        inputName: String,
        targetFormat: String,
        bitrate: String,
        onProgress: (Float) -> Unit
    ): Result<String> = withContext(Dispatchers.IO) {
        var tempInputFile: File? = null
        var tempOutputFile: File? = null

        try {
            // 1. Preparar archivo de entrada temporal
            val baseName = inputName.substringBeforeLast(".")
            val ext = inputName.substringAfterLast(".", "")
            tempInputFile = File(context.cacheDir, "input_${System.currentTimeMillis()}.$ext")

            context.contentResolver.openInputStream(inputUri)?.use { input ->
                FileOutputStream(tempInputFile).use { output ->
                    input.copyTo(output)
                }
            } ?: return@withContext Result.failure(Exception("No se pudo leer el archivo de entrada"))

            // 2. Preparar archivo de salida temporal
            val outputExt = targetFormat.lowercase().trimStart('.')
            tempOutputFile = File(context.cacheDir, "output_${System.currentTimeMillis()}.$outputExt")

            // 3. Construir comando FFmpeg
            val cmdList = mutableListOf<String>()
            cmdList.add("-y")
            cmdList.add("-i")
            cmdList.add(tempInputFile.absolutePath)
            cmdList.add("-vn") // Descartar cualquier pista de video

            val codecArgs = CODEC_MAP[outputExt] ?: listOf("-c:a", "libmp3lame")
            cmdList.addAll(codecArgs)

            // Formatos con bitrate
            if (outputExt !in listOf("wav", "flac", "aiff")) {
                cmdList.add("-b:a")
                cmdList.add(bitrate)
            }

            cmdList.add(tempOutputFile.absolutePath)

            val cmd = cmdList.joinToString(" ")

            // 4. Ejecutar FFmpeg
            val session = FFmpegKit.execute(cmd)
            val returnCode = session.returnCode

            if (ReturnCode.isSuccess(returnCode)) {
                // 5. Guardar el archivo en la carpeta publica de Musica
                val finalFileName = "$baseName.$outputExt"
                val savedPath = saveToPublicMusic(context, tempOutputFile, finalFileName, outputExt)
                Result.success(savedPath)
            } else {
                val outputLog = session.allLogsAsString
                Result.failure(Exception("Error FFmpeg (${returnCode?.value}): $outputLog"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        } finally {
            try {
                tempInputFile?.delete()
                tempOutputFile?.delete()
            } catch (_: Exception) {}
        }
    }

    private fun saveToPublicMusic(
        context: Context,
        sourceFile: File,
        fileName: String,
        extension: String
    ): String {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val contentValues = ContentValues().apply {
                put(MediaStore.Audio.Media.DISPLAY_NAME, fileName)
                put(MediaStore.Audio.Media.MIME_TYPE, getMimeType(extension))
                put(MediaStore.Audio.Media.RELATIVE_PATH, "${Environment.DIRECTORY_MUSIC}/ConvertedAudio")
                put(MediaStore.Audio.Media.IS_PENDING, 1)
            }

            val resolver = context.contentResolver
            val uri = resolver.insert(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, contentValues)
                ?: throw Exception("No se pudo crear el archivo en MediaStore")

            resolver.openOutputStream(uri)?.use { out ->
                sourceFile.inputStream().use { inStream ->
                    inStream.copyTo(out)
                }
            }

            contentValues.clear()
            contentValues.put(MediaStore.Audio.Media.IS_PENDING, 0)
            resolver.update(uri, contentValues, null, null)

            "Música/ConvertedAudio/$fileName"
        } else {
            val musicDir = File(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MUSIC),
                "ConvertedAudio"
            )
            if (!musicDir.exists()) musicDir.mkdirs()

            val destFile = File(musicDir, fileName)
            sourceFile.copyTo(destFile, overwrite = true)

            MediaScannerConnection.scanFile(
                context,
                arrayOf(destFile.absolutePath),
                arrayOf(getMimeType(extension)),
                null
            )

            destFile.absolutePath
        }
    }

    private fun getMimeType(ext: String): String {
        return when (ext.lowercase()) {
            "mp3" -> "audio/mpeg"
            "m4a", "aac" -> "audio/mp4"
            "wav" -> "audio/wav"
            "flac" -> "audio/flac"
            "ogg", "opus" -> "audio/ogg"
            "wma" -> "audio/x-ms-wma"
            else -> "audio/*"
        }
    }
}
