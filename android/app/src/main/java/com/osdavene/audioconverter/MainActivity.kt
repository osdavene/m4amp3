package com.osdavene.audioconverter

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.osdavene.audioconverter.ui.screens.MainScreen
import com.osdavene.audioconverter.ui.theme.AudioConverterTheme
import com.osdavene.audioconverter.ui.theme.DarkBg
import com.osdavene.audioconverter.viewmodel.ConverterViewModel

class MainActivity : ComponentActivity() {

    private val viewModel: ConverterViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AudioConverterTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = DarkBg
                ) {
                    MainScreen(viewModel = viewModel)
                }
            }
        }
    }
}
