// #include <string.h>
// #include <sys/socket.h>
// #include <netinet/in.h>
// #include <arpa/inet.h>
// #include <stdio.h>
// #include "freertos/FreeRTOS.h"
// #include "freertos/task.h"
// #include "esp_wifi.h"
// #include "esp_event.h"
// #include "esp_log.h"
// #include "nvs_flash.h"
// #include "esp_netif.h"
// #include <errno.h>

// #define WIFI_SSID    "Yuzhen的iPhone"      // Change to your WiFi SSID
// #define WIFI_PASS    "1234567890"          // Change to your WiFi password
// #define SERVER_IP    "172.20.10.2"         // Change to the PC server IP address
// #define SERVER_PORT  1234                  // Change to the port that the PC server is listening on

// static const char *TAG = "TCP_CLIENT";
 
// // WiFi event handler: handle connection, disconnection, IP acquisition, etc.
// static void wifi_event_handler(void *arg, esp_event_base_t event_base,
//                                int32_t event_id, void *event_data)
// {
//     if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
//         esp_wifi_connect();
//     } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
//         ESP_LOGI(TAG, "WiFi disconnected, attempting to reconnect...");
//         esp_wifi_connect();
//     } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
//         ip_event_got_ip_t *event = (ip_event_got_ip_t *) event_data;
//         ESP_LOGI(TAG, "Got IP address: " IPSTR, IP2STR(&event->ip_info.ip));
//     }
// }

// // Initialize WiFi in Station mode to connect to the specified SSID and password
// static void wifi_init_sta(void)
// {
//     // Initialize NVS
//     esp_err_t ret = nvs_flash_init();
//     if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
//         ESP_ERROR_CHECK(nvs_flash_erase());
//         ret = nvs_flash_init();
//     }
//     ESP_ERROR_CHECK(ret);

//     ESP_ERROR_CHECK(esp_netif_init());
//     ESP_ERROR_CHECK(esp_event_loop_create_default());
//     // Create default WiFi STA interface
//     esp_netif_create_default_wifi_sta();

//     wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
//     ESP_ERROR_CHECK(esp_wifi_init(&cfg));

//     ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
//                                                         ESP_EVENT_ANY_ID,
//                                                         &wifi_event_handler,
//                                                         NULL,
//                                                         NULL));
//     ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
//                                                         IP_EVENT_STA_GOT_IP,
//                                                         &wifi_event_handler,
//                                                         NULL,
//                                                         NULL));

//     wifi_config_t wifi_config = {
//         .sta = {
//             .ssid = WIFI_SSID,
//             .password = WIFI_PASS,
//         },
//     };
//     ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
//     ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
//     ESP_ERROR_CHECK(esp_wifi_start());

//     ESP_LOGI(TAG, "WiFi initialized, connecting...");
// }

// // TCP client task: connect to the server and send "hello" every 1 second
// static void tcp_client_task(void *pvParameters)
// {
//     const char payload[] = "hello\n";

//     while(1) {
//         // Create socket
//         int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
//         if (sock < 0) {
//             ESP_LOGE(TAG, "Failed to create socket: errno %d", errno);
//             vTaskDelay(1000 / portTICK_PERIOD_MS);
//             continue;
//         }
//         struct sockaddr_in dest_addr;
//         dest_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
//         dest_addr.sin_family = AF_INET;
//         dest_addr.sin_port = htons(SERVER_PORT);

//         ESP_LOGI(TAG, "Socket created, connecting to %s:%d", SERVER_IP, SERVER_PORT);

//         if (connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) != 0) {
//             ESP_LOGE(TAG, "Socket connection failed: errno %d", errno);
//             close(sock);
//             vTaskDelay(1000 / portTICK_PERIOD_MS);
//             continue;
//         }

//         ESP_LOGI(TAG, "Successfully connected to %s:%d", SERVER_IP, SERVER_PORT);

//         // Loop sending "hello" message every 1 second
//         while (1) {
//             int err = send(sock, payload, strlen(payload), 0);
//             if (err < 0) {
//                 ESP_LOGE(TAG, "Error sending data: errno %d", errno);
//                 break;
//             }
//             ESP_LOGI(TAG, "Message sent: %s", payload);
//             vTaskDelay(1000 / portTICK_PERIOD_MS);
//         }

//         if (sock != -1) {
//             ESP_LOGE(TAG, "Closing socket, preparing to reconnect...");
//             close(sock);
//         }
//         // After disconnection, wait for 1 second before reconnecting
//         vTaskDelay(1000 / portTICK_PERIOD_MS);
//     }
//     vTaskDelete(NULL);
// }

// void app_main(void)
// {
//     wifi_init_sta();
//     // Wait for WiFi to stabilize before starting the TCP client task
//     vTaskDelay(5000 / portTICK_PERIOD_MS);
//     xTaskCreate(tcp_client_task, "tcp_client_task", 4096, NULL, 5, NULL);
// }









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

#define WIFI_SSID    "Yuzhen的iPhone"      // 修改为你的 WiFi 名称
#define WIFI_PASS    "1234567890"          // 修改为你的 WiFi 密码
#define SERVER_IP    "172.20.10.2"         // PC 服务器 IP 地址
#define SERVER_PORT  1234                  // 服务器监听的端口

static const char *TAG = "TCP_PDM_CLIENT";

// WiFi事件处理函数：处理启动、断开、获取IP等事件
static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGI(TAG, "WiFi断开，正在尝试重连...");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *) event_data;
        ESP_LOGI(TAG, "获取到IP地址: " IPSTR, IP2STR(&event->ip_info.ip));
    }
}

// 初始化WiFi为STA模式
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

    ESP_LOGI(TAG, "WiFi初始化完毕，正在连接...");
}

// I2S 及 PDM 配置参数
#define I2S_SAMPLE_RATE    16000
#define I2S_READ_BUF_SIZE  512
#define PDM_CLK_GPIO       5
#define PDM_DATA_GPIO      6

// 用于控制录音状态的全局变量
volatile bool recording = true;

// TCP PDM任务：建立 TCP 连接，并读取 PDM 数据后发送到 PC
static void tcp_pdm_task(void *pvParameters)
{
    int sock = -1;
    struct sockaddr_in dest_addr;

    // 循环建立 TCP 连接
    while (1) {
        if (sock < 0) {
            sock = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
            if (sock < 0) {
                ESP_LOGE(TAG, "创建socket失败: errno %d", errno);
                vTaskDelay(1000 / portTICK_PERIOD_MS);
                continue;
            }
            dest_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
            dest_addr.sin_family = AF_INET;
            dest_addr.sin_port = htons(SERVER_PORT);
            ESP_LOGI(TAG, "Socket创建成功，正在连接 %s:%d", SERVER_IP, SERVER_PORT);
            if (connect(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) != 0) {
                ESP_LOGE(TAG, "Socket连接失败: errno %d", errno);
                close(sock);
                sock = -1;
                vTaskDelay(1000 / portTICK_PERIOD_MS);
                continue;
            }
            ESP_LOGI(TAG, "成功连接到 %s:%d", SERVER_IP, SERVER_PORT);
        }

        // 初始化I2S通道，用于PDM麦克风数据采集
        i2s_chan_handle_t rx_chan;
        i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
        chan_cfg.dma_desc_num  = 4;
        chan_cfg.dma_frame_num = I2S_READ_BUF_SIZE / 2;  // 16位数据：2字节
        i2s_new_channel(&chan_cfg, NULL, &rx_chan);

        i2s_pdm_rx_config_t pdm_rx_cfg = {
            .clk_cfg  = I2S_PDM_RX_CLK_DEFAULT_CONFIG(I2S_SAMPLE_RATE),
            .slot_cfg = I2S_PDM_RX_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
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

        // 持续循环：读取 PDM 数据并通过 TCP 发送
        while (1) {
            if (recording) {
                esp_err_t ret = i2s_channel_read(rx_chan, read_buffer, I2S_READ_BUF_SIZE, &bytes_read, portMAX_DELAY);
                if (ret == ESP_OK && bytes_read > 0) {
                    int err = send(sock, read_buffer, bytes_read, 0);
                    if (err < 0) {
                        ESP_LOGE(TAG, "数据发送错误: errno %d", errno);
                        break;  // 出错后跳出循环，准备重连socket
                    }
                    ESP_LOGI(TAG, "已发送 %d 字节数据", bytes_read);

                    err = send()
                }
            } else {
                vTaskDelay(100 / portTICK_PERIOD_MS);
            }
        }

        free(read_buffer);
        i2s_channel_disable(rx_chan);
        close(sock);
        sock = -1;
        ESP_LOGE(TAG, "Socket已关闭，正在重连...");
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
    vTaskDelete(NULL);
}

void app_main(void)
{
    // 1. 初始化WiFi
    wifi_init_sta();
    // 等待WiFi稳定连接
    vTaskDelay(5000 / portTICK_PERIOD_MS);
    // 2. 创建任务：采集PDM数据并通过TCP发送到PC
    xTaskCreate(tcp_pdm_task, "tcp_pdm_task", 8192, NULL, 5, NULL);
}
