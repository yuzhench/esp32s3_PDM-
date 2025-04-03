#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2s_pdm.h"
#include "esp_log.h"
#include "driver/uart.h"

#define TAG "PDM_RX_EXAMPLE"

#define I2S_SAMPLE_RATE    16000               // PCM sample rate (in Hz)
#define I2S_READ_BUF_SIZE  512                 // Read 512 bytes -> 256 x 16-bit samples

// Modify these GPIO pins according to your hardware setup
#define PDM_CLK_GPIO  5
#define PDM_DATA_GPIO 6

//uart pin distribution 
#define UART_PORT_NUM      UART_NUM_0
#define UART_BAUD_RATE     921600

volatile bool recording = true;

void pdm_mic_task(void *pvParam)
{
    // 1. Create an I2S channel (in Master mode)
    i2s_chan_handle_t rx_chan;
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    chan_cfg.dma_desc_num  = 4;               // Number of DMA descriptors
    chan_cfg.dma_frame_num = I2S_READ_BUF_SIZE / 2; // 16 bits = 2 bytes, so divide by 2

    i2s_new_channel(&chan_cfg, NULL, &rx_chan);

    // 2. Configure the PDM RX mode
    i2s_pdm_rx_config_t pdm_rx_cfg = {
        .clk_cfg  = I2S_PDM_RX_CLK_DEFAULT_CONFIG(I2S_SAMPLE_RATE),
        .slot_cfg = I2S_PDM_RX_SLOT_DEFAULT_CONFIG(
                        I2S_DATA_BIT_WIDTH_16BIT,
                        I2S_SLOT_MODE_MONO
                    ),
        .gpio_cfg = {
            .clk = PDM_CLK_GPIO,    // PDM clock out to microphone
            .din = PDM_DATA_GPIO,   // PDM data in from microphone
            .invert_flags = {
                .clk_inv = false,
            },
        },
    };

    i2s_channel_init_pdm_rx_mode(rx_chan, &pdm_rx_cfg);
    i2s_channel_enable(rx_chan);

    // Allocate a buffer for receiving PCM data
    uint8_t *read_buffer = (uint8_t *)malloc(I2S_READ_BUF_SIZE);
    size_t bytes_read = 0;


    //initialize the uart port 
    uart_config_t uart_config = {
        .baud_rate = UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        // 使用默认的 UART_NUM_0 TXD、RXD 引脚
    };
    uart_param_config(UART_PORT_NUM, &uart_config);
    uart_driver_install(UART_PORT_NUM, 2048, 0, 0, NULL, 0);


    while (1) {
        // 3. Block and read PCM data into read_buffer
        if (recording){
            esp_err_t ret = i2s_channel_read(rx_chan, read_buffer, I2S_READ_BUF_SIZE, &bytes_read, portMAX_DELAY);
            if (ret == ESP_OK && bytes_read > 0) {
                // read_buffer now contains 16-bit PCM audio samples (mono).
                // You can send them out, store them, or process them here.
    
                // Example: Print the first four samples
                // uint16_t *samples = (uint16_t *)read_buffer;
                // ESP_LOGI(TAG, "Data: %d %d %d %d ...", samples[0], samples[1], samples[2], samples[3]);
    
                //send the data through the uart port 
                uart_write_bytes(UART_PORT_NUM, (const char *)read_buffer, bytes_read);
    
            }
        }
        else { 
            //not recording, waiting 
            vTaskDelay(100 / portTICK_PERIOD_MS);
        }
    }

    free(read_buffer);
    vTaskDelete(NULL);
}


// void command_task(void *pvParam)
// {
//     uint8_t data;
//     while(1) {
//         //try to read only one byte and set the time limitation to be 20 ms
//         int len = uart_read_bytes(UART_PORT_NUM, &data, 1, 20 / portTICK_PERIOD_MS);
//         ESP_LOGI(TAG, "test command_task");
//         if (len > 0) {
//             if(data == ' ') {
//                 //flip the current recording state
//                 recording = !recording;
//                 if(recording) {
//                     ESP_LOGI(TAG, "start recording");
//                 } else {
//                     ESP_LOGI(TAG, "record stop");
//                 }
//             }
//         }
//         vTaskDelay(50 / portTICK_PERIOD_MS);
//     }
// //     vTaskDelete(NULL);
// }

void app_main(void)
{
    // Create the task that reads from the PDM microphone
    xTaskCreate(pdm_mic_task, "pdm_mic_task", 4096, NULL, 5, NULL);
    // xTaskCreate(command_task, "command_task", 4096, NULL, 5, NULL);

}
