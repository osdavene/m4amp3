package com.osdavene.audioconverter.service

import android.content.ContentValues
import android.content.Context
import android.media.MediaScannerConnection
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import com.arthenica.ffmpegkit.FFmpegKit
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
            // 1. Copiar archivo de entrada a cache temporal de forma segura
            val baseName = inputName.substringBeforeLast(".").ifBlank { "audio_${System.currentTimeMillis()}" }
            val ext = inputName.substringAfterLast(".", "tmp")
            tempInputFile = File(context.cacheDir, "in_${System.currentTimeMillis()}.$ext")

            val copied = runCatching {
                context.contentResolver.openInputStream(inputUri)?.use { input ->
                    FileOutputStream(tempInputFile).use { output ->
                        input.copyTo(output)
                    }
                }
            }.isSuccess

            if (!copied || !tempInputFile.exists() || tempInputFile.length() == 0L) {
                return@withContext Result.failure(Exception("No se pudo leer el archivo de origen ($inputName)"))
            }

            // 2. Preparar archivo de salida temporal
            val outputExt = targetFormat.lowercase().trimStart('.')
            tempOutputFile = File(context.cacheDir, "out_${System.currentTimeMillis()}.$outputExt")

            // 3. Construir lista de argumentos limpia para FFmpeg
            val args = mutableListOf<String>()
            args.add("-y")
            args.add("-i")
            args.add(tempInputFile.absolutePath)
            args.add("-vn") // Sin pista de video

            val codecArgs = CODEC_MAP[outputExt] ?: listOf("-c:a", "libmp3lame")
            args.addAll(codecArgs)

            // Bitrate para formatos comprimidos
            if (outputExt !in listOf("wav", "flac", "aiff")) {
                args.add("-b:a")
                args.add(bitrate)
            }

            args.add(tempOutputFile.absolutePath)

            // 4. Ejecutar FFmpeg con lista de argumentos segura (evita problemas de espacios)
            val session = FFmpegKit.executeWithArguments(args.toTypedArray())
            val returnCode = session.returnCode

            if (ReturnCode.isSuccess(returnCode)) {
                if (tempOutputFile.exists() && tempOutputFile.length() > 0L) {
                    val finalFileName = "$baseName.$outputExt"
                    val savedPath = saveToPublicMusic(context, tempOutputFile, finalFileName, outputExt)
                    Result.success(savedPath)
                } else {
                    Result.failure(Exception("El archivo convertido está vacío"))
                }
            } else {
                val errorLogs = session.allLogsAsString
                val failMsg = session.failStackTrace ?: errorLogs
                Result.failure(Exception("Fallo en FFmpeg (${returnCode?.value}): $failMsg"))
            }
        } catch (t: Throwable) {
            Result.failure(Exception(t.message ?: "Error inesperado durante la conversión", t))
        } finally {
            try {
                tempInputFile?.delete()
                tempOutputFile?.delete()
            } catch (_: Throwable) {}
        }
    }

    private fun saveToPublicMusic(
        context: Context,
        sourceFile: File,
        fileName: String,
        extension: String
    ): String {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val contentValues = ContentValues().apply {
                    put(MediaStore.Audio.Media.DISPLAY_NAME, fileName)
                    put(MediaStore.Audio.Media.MIME_TYPE, getMimeType(extension))
                    put(MediaStore.Audio.Media.RELATIVE_PATH, "${Environment.DIRECTORY_MUSIC}/ConvertedAudio")
                    put(MediaStore.Audio.Media.IS_PENDING, 1)
                }

                val resolver = context.contentResolver
                val uri = resolver.insert(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, contentValues)
                    ?: throw Exception("No se pudo crear entrada en MediaStore")

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
        } catch (e: Throwable) {
            // Fallback: guardar en carpeta privada de la app
            val fallbackDir = File(context.getExternalFilesDir(Environment.DIRECTORY_MUSIC), "ConvertedAudio")
            if (!fallbackDir.exists()) fallbackDir.mkdirs()
            val fallbackFile = File(fallbackDir, fileName)
            sourceFile.copyTo(fallbackFile, overwrite = true)
            fallbackFile.absolutePath
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
