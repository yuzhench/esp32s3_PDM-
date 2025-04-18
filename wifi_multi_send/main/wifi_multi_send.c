#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include <errno.h>
#include "driver/i2s_pdm.h"

#define WIFI_SSID    "Yuzhen的iPhone"      // Modify to your WiFi name
#define WIFI_PASS    "1234567890"         // Modify to your WiFi password
#define SERVER_IP    "172.20.10.2"        // PC server IP address

// #define WIFI_SSID    "Xinying iPhone"      // Modify to your WiFi name
// #define WIFI_PASS    "xinying25"         // Modify to your WiFi password
// #define SERVER_IP    "172.20.10.10" //"172.20.10.2"        // PC server IP address


#define SERVER_PORT  1234                 // Listening port

static const char *TAG = "TCP_PDM_CLIENT";

// WiFi event handler: handle start, disconnect, and IP acquisition events
static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGI(TAG, "WiFi disconnected, trying to reconnect...");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *) event_data;
        ESP_LOGI(TAG, "Acquired IP address: " IPSTR, IP2STR(&event->ip_info.ip));
    }
}

// Initialize Wi-Fi in STA mode
static void wifi_init_sta(void)
{
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        NULL));

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "WiFi initialized, connecting...");
}

// I2S and PDM configuration parameters
#define I2S_SAMPLE_RATE    16000
#define I2S_READ_BUF_SIZE  1024
#define PDM_CLK_GPIO       5
#define PDM_DATA_GPIO      6

// Global variable to control recording state
volatile bool recording = true;

// TCP PDM task: establish a TCP connection, then read PDM data and send to PC
static void tcp_pdm_task(void *pvParameters)
{
    int sock = -1;
    struct sockaddr_in dest_addr;

    // Continuously establish TCP connection
    while (1) {
        if (sock < 0) {
            sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
            if (sock < 0) {
                ESP_LOGE(TAG, "Failed to create socket: errno %d", errno);
                vTaskDelay(1000 / portTICK_PERIOD_MS);
                continue;
            }
            dest_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
            dest_addr.sin_family = AF_INET;
            dest_addr.sin_port = htons(SERVER_PORT);
            ESP_LOGI(TAG, "Socket created successfully, connecting to %s:%d", SERVER_IP, SERVER_PORT);
            if (connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) != 0) {
                ESP_LOGE(TAG, "Failed to connect: errno %d", errno);
                close(sock);
                sock = -1;
                vTaskDelay(1000 / portTICK_PERIOD_MS);
                continue;
            }
            ESP_LOGI(TAG, "Connected to %s:%d", SERVER_IP, SERVER_PORT);
        }

        // Initialize the I2S channel for PDM microphone data acquisition
        i2s_chan_handle_t rx_chan;
        i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
        chan_cfg.dma_desc_num  = 4;
        chan_cfg.dma_frame_num = I2S_READ_BUF_SIZE / 2;  // 16-bit data: 2 bytes
        i2s_new_channel(&chan_cfg, NULL, &rx_chan);

        i2s_pdm_rx_config_t pdm_rx_cfg = {
            .clk_cfg  = I2S_PDM_RX_CLK_DEFAULT_CONFIG(I2S_SAMPLE_RATE),
            .slot_cfg = I2S_PDM_RX_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO),
            .gpio_cfg = {
                .clk = PDM_CLK_GPIO,
                .din = PDM_DATA_GPIO,
                .invert_flags = {
                    .clk_inv = false,
                },
            },
        };

        i2s_channel_init_pdm_rx_mode(rx_chan, &pdm_rx_cfg);
        i2s_channel_enable(rx_chan);

        uint8_t *read_buffer = (uint8_t *)malloc(I2S_READ_BUF_SIZE);
        size_t bytes_read = 0;

        // Initialize the counter
        uint8_t counter = 0;
        // Continuously read PDM data and send via TCP
        while (1) {
            if (recording) {
                esp_err_t ret = i2s_channel_read(rx_chan, read_buffer, I2S_READ_BUF_SIZE, &bytes_read, portMAX_DELAY);
                if (ret == ESP_OK && bytes_read > 0) {

                    // Build packet length (I2S_READ_BUF_SIZE + 1 for counter)
                    uint16_t packet_length = I2S_READ_BUF_SIZE + 1;
                    // Convert to network byte order (big-endian)
                    uint16_t net_packet_length = htons(packet_length);

                    int err = 0;

                    // 1. Send 2-byte header (total packet length)
                    err = send(sock, &net_packet_length, sizeof(net_packet_length), 0);
                    if (err < 0) {
                        ESP_LOGE(TAG, "Header send error: errno %d", errno);
                        return;
                    }

                    // 2. Send audio data
                    err = send(sock, read_buffer, bytes_read, 0);
                    if (err < 0) {
                        ESP_LOGE(TAG, "Audio data send error: errno %d", errno);
                        return;
                    }

                    // 3. Send 1-byte counter
                    err = send(sock, &counter, 1, 0);
                    if (err < 0) {
                        ESP_LOGE(TAG, "Counter send error: errno %d", errno);
                        return;
                    }

                    ESP_LOGI(TAG, "Sent %d bytes of audio data, counter: %d", bytes_read, counter);
                    // Increment counter (note that 1 byte will overflow after 255)
                    counter++;
                }
            } else {
                vTaskDelay(100 / portTICK_PERIOD_MS);
            }
        }

        free(read_buffer);
        i2s_channel_disable(rx_chan);
        close(sock);
        sock = -1;
        ESP_LOGE(TAG, "Socket closed, reconnecting...");
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
    vTaskDelete(NULL);
}

void app_main(void)
{
    // 1. Initialize Wi-Fi
    wifi_init_sta();
    // Wait for Wi-Fi to connect
    vTaskDelay(5000 / portTICK_PERIOD_MS);
    // 2. Create the task: capture PDM data and send to PC via TCP
    xTaskCreate(tcp_pdm_task, "tcp_pdm_task", 8192, NULL, 5, NULL);
}
