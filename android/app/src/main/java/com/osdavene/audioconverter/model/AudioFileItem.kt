package com.osdavene.audioconverter.model

import android.net.Uri

enum class ConversionStatus {
    IDLE,
    CONVERTING,
    SUCCESS,
    ERROR
}

data class AudioFileItem(
    val id: String = java.util.UUID.randomUUID().toString(),
    val uri: Uri,
    val name: String,
    val sizeBytes: Long = 0,
    val extension: String = "",
    val status: ConversionStatus = ConversionStatus.IDLE,
    val progress: Float = 0f,
    val outputPath: String? = null,
    val errorMessage: String? = null
) {
    val formattedSize: String
        get() {
            if (sizeBytes <= 0) return "Desconocido"
            val kb = sizeBytes / 1024.0
            val mb = kb / 1024.0
            val gb = mb / 1024.0
            return when {
                gb >= 1.0 -> String.format("%.2f GB", gb)
                mb >= 1.0 -> String.format("%.2f MB", mb)
                kb >= 1.0 -> String.format("%.1f KB", kb)
                else -> "$sizeBytes B"
            }
        }
}
