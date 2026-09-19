package com.osdavene.audioconverter.ui.screens

import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.osdavene.audioconverter.ui.components.FileItemCard
import com.osdavene.audioconverter.ui.components.FormatSelector
import com.osdavene.audioconverter.ui.components.QualitySelector
import com.osdavene.audioconverter.ui.theme.*
import com.osdavene.audioconverter.viewmodel.ConverterViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    viewModel: ConverterViewModel,
    modifier: Modifier = Modifier
) {
    val selectedFiles by viewModel.selectedFiles.collectAsState()
    val targetFormat by viewModel.targetFormat.collectAsState()
    val targetBitrate by viewModel.targetBitrate.collectAsState()
    val isConverting by viewModel.isConverting.collectAsState()
    val globalProgress by viewModel.globalProgress.collectAsState()
    val statusMessage by viewModel.statusMessage.collectAsState()

    // Selector de múltiples archivos de audio nativo de Android
    val openFilesLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenMultipleDocuments()
    ) { uris: List<Uri> ->
        if (uris.isNotEmpty()) {
            viewModel.addUris(uris)
        }
    }

    // Selector de carpeta completa (árbol de documentos)
    val openTreeLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocumentTree()
    ) { treeUri: Uri? ->
        treeUri?.let { uri ->
            viewModel.addFolderTree(uri)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Conversor de Audio",
                            style = MaterialTheme.typography.titleLarge,
                            color = TextPrimary
                        )
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(RoundedCornerShape(3.dp))
                                    .background(AccentEmerald)
                            )
                            Text(
                                text = "100% Offline • Motor FFmpeg Nativo",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary,
                                fontSize = 11.sp
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DarkBg,
                    titleContentColor = TextPrimary
                )
            )
        },
        bottomBar = {
            // Botonera de Conversion Inferior
            Surface(
                color = DarkSurface,
                tonalElevation = 8.dp,
                shadowElevation = 16.dp
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 12.dp)
                        .navigationBarsPadding()
                ) {
                    // Progreso Global
                    AnimatedVisibility(visible = isConverting || globalProgress > 0f) {
                        Column(modifier = Modifier.padding(bottom = 8.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = statusMessage,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = TextSecondary,
                                    fontSize = 12.sp
                                )
                                Text(
                                    text = "${(globalProgress * 100).toInt()}%",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = SecondaryCyan,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp
                                )
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            LinearProgressIndicator(
                                progress = { globalProgress },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(8.dp)
                                    .clip(RoundedCornerShape(4.dp)),
                                color = PrimaryIndigo,
                                trackColor = DarkSurfaceVariant
                            )
                        }
                    }

                    if (isConverting) {
                        Button(
                            onClick = { viewModel.cancelConversion() },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(52.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = ErrorRose)
                        ) {
                            Icon(Icons.Default.Close, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Cancelar Conversión",
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }
                    } else {
                        Button(
                            onClick = { viewModel.startConversion() },
                            enabled = selectedFiles.isNotEmpty(),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(52.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = PrimaryIndigo,
                                disabledContainerColor = DarkSurfaceVariant
                            )
                        ) {
                            Icon(Icons.Default.Bolt, contentDescription = null, tint = TextPrimary)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = if (selectedFiles.isEmpty()) "Selecciona archivos para convertir" else "Comenzar Conversión (${selectedFiles.size})",
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp,
                                color = if (selectedFiles.isEmpty()) TextMuted else TextPrimary
                            )
                        }
                    }
                }
            }
        },
        containerColor = DarkBg
    ) { innerPadding ->
        LazyColumn(
            modifier = modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            // 1. Botones para Seleccionar Archivos
            item {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Button(
                        onClick = {
                            openFilesLauncher.launch(
                                arrayOf(
                                    "audio/*",
                                    "video/*",
                                    "application/ogg",
                                    "*/*"
                                )
                            )
                        },
                        enabled = !isConverting,
                        modifier = Modifier
                            .weight(1f)
                            .height(50.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryIndigo)
                    ) {
                        Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(20.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Elegir Audios",
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 14.sp
                        )
                    }

                    OutlinedButton(
                        onClick = {
                            openTreeLauncher.launch(null)
                        },
                        enabled = !isConverting,
                        modifier = Modifier
                            .weight(1f)
                            .height(50.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = SecondaryCyan),
                        border = androidx.compose.foundation.BorderStroke(1.5.dp, SecondaryCyan)
                    ) {
                        Icon(Icons.Default.FolderOpen, contentDescription = null, modifier = Modifier.size(20.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "+ Carpeta",
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 14.sp
                        )
                    }
                }
            }

            // 2. Selectores de Formato y Bitrate
            item {
                FormatSelector(
                    selectedFormat = targetFormat,
                    onFormatSelected = { viewModel.setTargetFormat(it) }
                )
            }

            item {
                QualitySelector(
                    selectedBitrate = targetBitrate,
                    onBitrateSelected = { viewModel.setTargetBitrate(it) }
                )
            }

            // 3. Encabezado de Lista de Archivos
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Archivos Seleccionados (${selectedFiles.size})",
                        style = MaterialTheme.typography.titleMedium,
                        color = TextPrimary
                    )
                    if (selectedFiles.isNotEmpty() && !isConverting) {
                        TextButton(
                            onClick = { viewModel.clearAll() },
                            colors = ButtonDefaults.textButtonColors(contentColor = ErrorRose)
                        ) {
                            Text(
                                text = "Limpiar Todo",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }
                }
            }

            // 4. Lista de Archivos o Estado Vacio
            if (selectedFiles.isEmpty()) {
                item {
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 16.dp),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = DarkSurface)
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 36.dp, horizontal = 16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Icon(
                                Icons.Default.Audiotrack,
                                contentDescription = null,
                                tint = TextMuted,
                                modifier = Modifier.size(48.dp)
                            )
                            Spacer(modifier = Modifier.height(12.dp))
                            Text(
                                text = "No hay archivos seleccionados",
                                style = MaterialTheme.typography.titleMedium,
                                color = TextPrimary
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Toca '+ Elegir Audios' para comenzar",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextMuted,
                                fontSize = 13.sp
                            )
                        }
                    }
                }
            } else {
                items(selectedFiles, key = { it.id }) { item ->
                    FileItemCard(
                        item = item,
                        isConverting = isConverting,
                        onRemove = { viewModel.removeFile(item) }
                    )
                }
            }

            // Espacio al final para no tapar contenido con la barra inferior
            item {
                Spacer(modifier = Modifier.height(20.dp))
            }
        }
    }
}
