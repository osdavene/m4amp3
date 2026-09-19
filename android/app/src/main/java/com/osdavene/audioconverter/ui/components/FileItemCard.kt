package com.osdavene.audioconverter.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Audiotrack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Error
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.osdavene.audioconverter.model.AudioFileItem
import com.osdavene.audioconverter.model.ConversionStatus
import com.osdavene.audioconverter.ui.theme.*

@Composable
fun FileItemCard(
    item: AudioFileItem,
    isConverting: Boolean,
    onRemove: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = DarkSurface)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Icono de audio circular
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CircleShape)
                        .background(
                            when (item.status) {
                                ConversionStatus.SUCCESS -> AccentEmerald.copy(alpha = 0.2f)
                                ConversionStatus.ERROR -> ErrorRose.copy(alpha = 0.2f)
                                ConversionStatus.CONVERTING -> SecondaryCyan.copy(alpha = 0.2f)
                                else -> PrimaryIndigo.copy(alpha = 0.2f)
                            }
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    when (item.status) {
                        ConversionStatus.SUCCESS -> Icon(
                            Icons.Default.Check,
                            contentDescription = "Completado",
                            tint = AccentEmerald,
                            modifier = Modifier.size(20.dp)
                        )
                        ConversionStatus.ERROR -> Icon(
                            Icons.Default.Error,
                            contentDescription = "Error",
                            tint = ErrorRose,
                            modifier = Modifier.size(20.dp)
                        )
                        else -> Icon(
                            Icons.Default.Audiotrack,
                            contentDescription = "Audio",
                            tint = if (item.status == ConversionStatus.CONVERTING) SecondaryCyan else PrimaryIndigo,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.width(12.dp))

                // Nombre y detalles del archivo
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = item.name,
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.Medium,
                        color = TextPrimary,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = item.extension.uppercase(),
                            style = MaterialTheme.typography.bodyMedium,
                            color = SecondaryCyan,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp
                        )
                        Text(
                            text = "•",
                            style = MaterialTheme.typography.bodyMedium,
                            color = TextMuted
                        )
                        Text(
                            text = item.formattedSize,
                            style = MaterialTheme.typography.bodyMedium,
                            color = TextSecondary,
                            fontSize = 12.sp
                        )
                    }
                }

                // Botón eliminar (solo si no está convirtiendo)
                if (!isConverting) {
                    IconButton(
                        onClick = onRemove,
                        modifier = Modifier.size(36.dp)
                    ) {
                        Icon(
                            Icons.Default.Close,
                            contentDescription = "Eliminar",
                            tint = TextMuted,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                }
            }

            // Barra de progreso individual si está convirtiendo
            AnimatedVisibility(visible = item.status == ConversionStatus.CONVERTING) {
                Column(modifier = Modifier.padding(top = 8.dp)) {
                    LinearProgressIndicator(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(6.dp)
                            .clip(RoundedCornerShape(3.dp)),
                        color = SecondaryCyan,
                        trackColor = DarkSurfaceVariant
                    )
                }
            }

            // Mensaje de resultado o error
            if (item.status == ConversionStatus.SUCCESS && item.outputPath != null) {
                Text(
                    text = "Guardado en: ${item.outputPath}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = AccentEmerald,
                    fontSize = 11.sp,
                    modifier = Modifier.padding(top = 6.dp)
                )
            } else if (item.status == ConversionStatus.ERROR && item.errorMessage != null) {
                Text(
                    text = "Error: ${item.errorMessage}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = ErrorRose,
                    fontSize = 11.sp,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 6.dp)
                )
            }
        }
    }
}
