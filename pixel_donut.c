#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <fcntl.h>
#include <zlib.h>
#include <stdint.h>

#define WIDTH 450
#define HEIGHT 450
#define BUFFER_SIZE (WIDTH * HEIGHT * 4)

static const char b64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

// 高性能 Base64 编码器
void base64_encode(const uint8_t *data, size_t input_length, char *encoded_data) {
    size_t i = 0, j = 0;
    while (i < input_length) {
        uint32_t octet_a = i < input_length ? data[i++] : 0;
        uint32_t octet_b = i < input_length ? data[i++] : 0;
        uint32_t octet_c = i < input_length ? data[i++] : 0;

        uint32_t triple = (octet_a << 0x10) + (octet_b << 0x08) + octet_c;

        encoded_data[j++] = b64_chars[(triple >> 18) & 0x3F];
        encoded_data[j++] = b64_chars[(triple >> 12) & 0x3F];
        encoded_data[j++] = (i > input_length + 1) ? '=' : b64_chars[(triple >> 6) & 0x3F];
        encoded_data[j++] = (i > input_length) ? '=' : b64_chars[triple & 0x3F];
    }
    encoded_data[j] = '\0';
}

void write_u32(uint8_t *buf, uint32_t val) {
    buf[0] = (val >> 24) & 0xFF;
    buf[1] = (val >> 16) & 0xFF;
    buf[2] = (val >> 8)  & 0xFF;
    buf[3] = val         & 0xFF;
}

// 内存级 PNG 编码器
uint8_t* encode_png(const uint8_t *rgba_data, int width, int height, size_t *out_len) {
    size_t scanline_size = 1 + width * 4;
    size_t raw_size = height * scanline_size;
    uint8_t *scanlines = malloc(raw_size);
    for (int r = 0; r < height; r++) {
        scanlines[r * scanline_size] = 0; // Filter type 0
        memcpy(scanlines + r * scanline_size + 1, rgba_data + r * width * 4, width * 4);
    }

    uLongf max_compressed_size = compressBound(raw_size);
    uint8_t *compressed_data = malloc(max_compressed_size);
    
    z_stream stream;
    stream.zalloc = Z_NULL;
    stream.zfree = Z_NULL;
    stream.opaque = Z_NULL;
    
    // 初始化 zlib deflate 流，压缩等级设为 1 (Z_BEST_SPEED)，提速数倍并减轻终端解压负担
    deflateInit2(&stream, 1, Z_DEFLATED, 15, 8, Z_DEFAULT_STRATEGY);
    stream.next_in = scanlines;
    stream.avail_in = raw_size;
    stream.next_out = compressed_data;
    stream.avail_out = max_compressed_size;
    
    deflate(&stream, Z_FINISH);
    uLong compressed_actual_size = stream.total_out;
    deflateEnd(&stream);
    free(scanlines);

    size_t png_size = 8 + 25 + (12 + compressed_actual_size) + 12;
    uint8_t *png = malloc(png_size);
    size_t p = 0;

    memcpy(png + p, "\x89PNG\r\n\x1a\n", 8); p += 8;

    write_u32(png + p, 13); p += 4;
    memcpy(png + p, "IHDR", 4); p += 4;
    write_u32(png + p, width); p += 4;
    write_u32(png + p, height); p += 4;
    png[p++] = 8;
    png[p++] = 6;  // RGBA
    png[p++] = 0;
    png[p++] = 0;
    png[p++] = 0;
    uint32_t ihdr_crc = crc32(0L, Z_NULL, 0);
    ihdr_crc = crc32(ihdr_crc, png + p - 17, 17);
    write_u32(png + p, ihdr_crc); p += 4;

    write_u32(png + p, compressed_actual_size); p += 4;
    memcpy(png + p, "IDAT", 4); p += 4;
    memcpy(png + p, compressed_data, compressed_actual_size); p += compressed_actual_size;
    free(compressed_data);
    
    uint32_t idat_crc = crc32(0L, Z_NULL, 0);
    idat_crc = crc32(idat_crc, png + p - compressed_actual_size - 4, compressed_actual_size + 4);
    write_u32(png + p, idat_crc); p += 4;

    write_u32(png + p, 0); p += 4;
    memcpy(png + p, "IEND", 4); p += 4;
    uint32_t iend_crc = crc32(0L, Z_NULL, 0);
    iend_crc = crc32(iend_crc, (const Bytef*)"IEND", 4);
    write_u32(png + p, iend_crc); p += 4;

    *out_len = png_size;
    return png;
}

void send_image_via_kitty(const uint8_t *png_data, size_t png_len, int target_cols, int target_rows) {
    // 1. 在内存中静默且前置完成 Base64 编码，确保后面 PTY I/O 输出具有极致的连续性
    size_t b64_len = 4 * ((png_len + 2) / 3);
    char *b64 = malloc(b64_len + 1);
    base64_encode(png_data, png_len, b64);

    // 2. 写入显式释放上一帧 GPU 显存纹理的 Kitty 协议指令
    //    由于我们在此处及后面数据块传输期间彻底移除了任何 fflush 调用，
    //    “删除指令”与“新图传输指令”会在同一个 PTY 原子刷新包中同时抵达终端。
    //    这在完美销毁历史显存、杜绝泄漏的同时，让终端来不及发生任何排版 Layout 抖动！
    printf("\033_Ga=d,i=2\033\\");

    size_t chunk_size = 4096;
    if (b64_len <= chunk_size) {
        printf("\033_Gf=100,a=T,i=2,q=2,c=%d,r=%d,m=0;%s\033\\\n", target_cols, target_rows, b64);
    } else {
        printf("\033_Gf=100,a=T,i=2,q=2,c=%d,r=%d,m=1;", target_cols, target_rows);
        fwrite(b64, 1, chunk_size, stdout);
        printf("\033\\");

        size_t idx = chunk_size;
        while (idx < b64_len - chunk_size) {
            printf("\033_Gm=1;");
            fwrite(b64 + idx, 1, chunk_size, stdout);
            printf("\033\\");
            idx += chunk_size;
        }
        printf("\033_Gm=0;%s\033\\\n", b64 + idx);
    }
    
    // 3. 仅在整帧图像流彻底输出完毕后，执行唯一的一次物理刷写
    fflush(stdout);
    free(b64);
}

int get_key_nonblocking() {
    struct timeval tv = {0, 0};
    fd_set fds;
    FD_ZERO(&fds);
    FD_SET(STDIN_FILENO, &fds);
    select(STDIN_FILENO + 1, &fds, NULL, NULL, &tv);
    if (FD_ISSET(STDIN_FILENO, &fds)) {
        char c;
        if (read(STDIN_FILENO, &c, 1) == 1) {
            return c;
        }
    }
    return 0;
}

int main() {
    uint8_t *buffer = malloc(BUFFER_SIZE);
    float *z_buffer = malloc(WIDTH * HEIGHT * sizeof(float));
    uint8_t *buffer_back = malloc(BUFFER_SIZE);
    float *z_buffer_back = malloc(WIDTH * HEIGHT * sizeof(float));

    // 调整几何常数与相机距离，完美避免穿透和裁剪
    const float R1 = 1.0f;          // 甜甜圈主环半径
    const float R2 = 0.5f;          // 管道横截面管径半径
    const float distance = 5.0f;    // 增大相机观察距离，彻底解决穿透露底问题
    const float scale = WIDTH * 0.60f; // 相应调整投影比例，增加到原先的 1.5 倍体积，画面极其宏伟饱满

    float angle_x = 0.0f;
    float angle_y = 0.0f;
    float angle_z = 0.0f;

    int material_mode = 0; // 0: 电影级黏土 (Clay), 1: 水晶玻璃 (Glass)

    const int TARGET_FPS = 60;
    const double FRAME_DURATION = 1.0 / TARGET_FPS;

    // 配置非阻塞原生终端属性
    struct termios old_settings, new_settings;
    tcgetattr(STDIN_FILENO, &old_settings);
    new_settings = old_settings;
    new_settings.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &new_settings);

    // 隐藏文本光标，并清屏
    printf("\033[?25l\033[2J\033[H");
    fflush(stdout);

    while (1) {
        struct timespec frame_start;
        clock_gettime(CLOCK_MONOTONIC, &frame_start);

        int key = get_key_nonblocking();
        if (key != 0) {
            if (key == 's' || key == 'S') {
                material_mode = 1 - material_mode; // 切换材质
            } else if (key == 'q' || key == 'Q' || key == 27) { // Q, q, or ESC
                break;
            }
        }

        struct winsize w;
        ioctl(STDOUT_FILENO, TIOCGWINSZ, &w);
        int columns = w.ws_col > 0 ? w.ws_col : 80;
        int rows = w.ws_row > 0 ? w.ws_row : 40;

        int target_rows = (int)(rows * 0.75);
        int target_cols = target_rows * 2;

        if (target_rows > rows - 4) target_rows = rows - 4;
        if (target_cols > columns - 4) target_cols = columns - 4;

        int start_row = (rows - target_rows) / 2;
        int start_col = (columns - target_cols) / 2;
        if (start_row < 1) start_row = 1;
        if (start_col < 1) start_col = 1;

        // 极速重置画布与 Z-Buffer
        memset(buffer, 0, BUFFER_SIZE);
        memset(z_buffer, 0, WIDTH * HEIGHT * sizeof(float));
        if (material_mode == 1) {
            memset(buffer_back, 0, BUFFER_SIZE);
            memset(z_buffer_back, 0, WIDTH * HEIGHT * sizeof(float));
        }

        float cos_A = cosf(angle_x), sin_A = sinf(angle_x);
        float cos_B = cosf(angle_y), sin_B = sinf(angle_y);

        // ==============================================================
        // ⚡ 终极图形学重构：单像素高精度 Z-Buffer 渲染 + 电影级黏土着色模型
        // ==============================================================
        // 1. 彻底根治黑屏：恢复标准的、绝对精准的单像素 Z-Buffer 测试与 100% 亮度写入，
        //    从投影和遮挡逻辑上彻底根除任何深度越权抢占漏洞，恢复最饱满高级的明暗灰阶。
        // 2. Cinematic Clay 光影：高保真双光源系统 + Half-Lambert 阴影包裹 + 菲涅尔超细
        //    白色外轮廓发光线（Fresnel Rim Light） + Blinn-Phong 湿润微亮抛光陶瓷高光亮点。
        // ==============================================================
        for (float theta = 0.0f; theta < 6.28318f; theta += 0.02f) {
            float costheta = cosf(theta);
            float sintheta = sinf(theta);

            float circle_x = R1 + R2 * costheta;
            float circle_y = R2 * sintheta;

            for (float phi = 0.0f; phi < 6.28318f; phi += 0.006f) {
                float cosphi = cosf(phi);
                float sinphi = sinf(phi);

                float x = circle_x * cosphi;
                float y = circle_y;
                float z = circle_x * sinphi;

                // 绕 X/Y 轴旋转矩阵
                float y1 = y * cos_A - z * sin_A;
                float z1 = y * sin_A + z * cos_A;
                float x2 = x * cos_B + z1 * sin_B;
                float z2 = -x * sin_B + z1 * cos_B;

                float z_depth = z2 + distance;
                float ooz = 1.0f / z_depth;

                // 精确四舍五入投影
                float xpf = WIDTH / 2.0f + (x2 * scale) * ooz;
                float ypf = HEIGHT / 2.0f + (y1 * scale) * ooz;
                int xp = (int)(xpf + 0.5f);
                int yp = (int)(ypf + 0.5f);

                // 计算法向量
                float ny1 = sintheta * cos_A - costheta * sinphi * sin_A;
                float nz1 = sintheta * sin_A + costheta * sinphi * cos_A;
                float nx2 = costheta * cosphi * cos_B + nz1 * sin_B;
                float nz2 = -costheta * cosphi * sin_B + nz1 * cos_B;

                // ================= 高阶着色模型 =================
                // (a) 双光源半兰伯特漫反射 (Half-Lambert)
                // 主光源 L1 = [0.0f, 0.707f, -0.707f] (左上)
                float dot1 = 0.707f * (ny1 - nz2);
                float diffuse1 = (dot1 * 0.5f + 0.5f) * (dot1 * 0.5f + 0.5f);

                // 辅光源 L2 = [0.577f, -0.462f, 0.577f] (右下，微弱补光)
                float dot2 = 0.577f * nx2 - 0.462f * ny1 + 0.577f * nz2;
                float diffuse2 = (dot2 * 0.5f + 0.5f) * (dot2 * 0.5f + 0.5f);
                
                float diffuse_total = 0.78f * diffuse1 + 0.22f * diffuse2;

                // (b) Blinn-Phong 湿润陶瓷镜面高光 (H = [0.0f, 0.383f, -0.924f])
                float spec_dot = 0.383f * ny1 - 0.924f * nz2;
                if (spec_dot < 0.0f) spec_dot = 0.0f;
                float specular = powf(spec_dot, 32.0f) * 0.48f; // 32 次强幂产生极精致高亮的白圆点

                // (c) 菲涅尔优雅白色轮廓边缘光 (Fresnel Rim Light，视线 V = [0, 0, -1])
                float cos_theta = fabsf(nz2); // 法线与视线夹角余弦
                float fresnel = powf(1.0f - cos_theta, 3.5f) * 0.28f; // 超细白光包裹圈

                // (d) 分支材质着色计算与深度测试写入
                if (xp >= 0 && xp < WIDTH && yp >= 0 && yp < HEIGHT) {
                    int idx = yp * WIDTH + xp;
                    int idx_rgba = idx * 4;
                    
                    if (nz2 <= 0.0f) {
                        // ============ Front-Face (前表面，朝向相机) ============
                        if (ooz > z_buffer[idx]) {
                            z_buffer[idx] = ooz;
                            
                            if (material_mode == 0) {
                                // 🎨 (Clay) 电影级黏土着色
                                float clay_val = diffuse_total * 0.72f + specular + fresnel;
                                int gray_val = (int)(255.0f * clay_val);
                                if (gray_val < 0) gray_val = 0;
                                if (gray_val > 255) gray_val = 255;
                                
                                buffer[idx_rgba]     = gray_val;
                                buffer[idx_rgba + 1] = gray_val;
                                buffer[idx_rgba + 2] = gray_val;
                                buffer[idx_rgba + 3] = 255;
                            } else {
                                // 💎 (Glass) 纯净透明水晶玻璃前表面着色器 (纯白反射高保真)
                                float cos_theta_g = fabsf(nz2);
                                float F0 = 0.08f;
                                float fresnel_glass = F0 + (1.0f - F0) * powf(1.0f - cos_theta_g, 4.0f);
                                
                                // 前表面极尖锐双镜面高光 (亮白反光点)
                                float spec_dot1 = 0.383f * ny1 - 0.924f * nz2;
                                if (spec_dot1 < 0.0f) spec_dot1 = 0.0f;
                                float spec_glass1 = powf(spec_dot1, 80.0f) * 0.95f;
                                
                                float spec_dot2 = 0.577f * nx2 - 0.462f * ny1 + 0.577f * nz2;
                                if (spec_dot2 < 0.0f) spec_dot2 = 0.0f;
                                float spec_glass2 = powf(spec_dot2, 40.0f) * 0.25f;
                                float spec_total = spec_glass1 + spec_glass2;
                                
                                // 正常水晶无色反射色彩公式 (R=G=B，彻底消除色彩偏置与彩虹圈圈走样)
                                float crystal_val = (fresnel_glass * 0.85f + spec_total);
                                int gray_val = (int)(255.0f * crystal_val);
                                if (gray_val < 0) gray_val = 0;
                                if (gray_val > 255) gray_val = 255;
                                
                                // 动态 Alpha：中部极度透明，边缘强反光极不透明
                                int alpha_int = (int)(255.0f * (fresnel_glass * 0.92f + spec_total * 0.2f));
                                if (alpha_int < 18) alpha_int = 18; // 保留最微弱的水晶轮廓
                                if (alpha_int > 255) alpha_int = 255;
                                
                                buffer[idx_rgba]     = gray_val;
                                buffer[idx_rgba + 1] = gray_val;
                                buffer[idx_rgba + 2] = gray_val;
                                buffer[idx_rgba + 3] = alpha_int;
                            }
                        }
                    } else if (material_mode == 1) {
                        // ============ Back-Face (后表面，背向相机，仅在玻璃模式下渲染) ============
                        if (ooz > z_buffer_back[idx]) {
                            z_buffer_back[idx] = ooz;
                            
                            float cos_theta_g = fabsf(nz2);
                            float F0 = 0.08f;
                            float fresnel_glass = F0 + (1.0f - F0) * powf(1.0f - cos_theta_g, 4.0f);
                            
                            // 后表面高光 (无色偏高保真水晶后壁反射)
                            float spec_dot1 = 0.383f * ny1 - 0.924f * nz2;
                            if (spec_dot1 < 0.0f) spec_dot1 = 0.0f;
                            float spec_glass1 = powf(spec_dot1, 60.0f) * 0.55f; // 稍微变暗
                            
                            float crystal_val = (fresnel_glass * 0.75f + spec_glass1);
                            int gray_val = (int)(255.0f * crystal_val);
                            if (gray_val < 0) gray_val = 0; if (gray_val > 255) gray_val = 255;
                            
                            // 后表面的菲涅尔反射与透射 Alpha 计算
                            int alpha_int = (int)(255.0f * (fresnel_glass * 0.75f + spec_glass1 * 0.1f));
                            if (alpha_int < 12) alpha_int = 12;
                            if (alpha_int > 255) alpha_int = 255;
                            
                            buffer_back[idx_rgba]     = gray_val;
                            buffer_back[idx_rgba + 1] = gray_val;
                            buffer_back[idx_rgba + 2] = gray_val;
                            buffer_back[idx_rgba + 3] = alpha_int;
                        }
                    }
                }
            }
        }

        // ==============================================================
        // 💎 终极图形学重构：双层玻璃物理透射混合 (Transmission Blend Pass)
        // ==============================================================
        // 如果是玻璃材质，我们将前表面的反射/镜面光与后表面透射过来的光进行物理 Alpha 合成。
        // ==============================================================
        if (material_mode == 1) {
            for (int i = 0; i < WIDTH * HEIGHT; i++) {
                int idx_rgba = i * 4;
                if (buffer_back[idx_rgba + 3] > 0) {
                    if (buffer[idx_rgba + 3] > 0) {
                        float r_f = buffer[idx_rgba] / 255.0f;
                        float g_f = buffer[idx_rgba + 1] / 255.0f;
                        float b_f = buffer[idx_rgba + 2] / 255.0f;
                        float a_f = buffer[idx_rgba + 3] / 255.0f;
                        
                        float r_b = buffer_back[idx_rgba] / 255.0f;
                        float g_b = buffer_back[idx_rgba + 1] / 255.0f;
                        float b_b = buffer_back[idx_rgba + 2] / 255.0f;
                        float a_b = buffer_back[idx_rgba + 3] / 255.0f;
                        
                        // 物理混合公式 (双层玻璃折射吸光透射)
                        float a_final = 1.0f - (1.0f - a_f) * (1.0f - a_b);
                        if (a_final > 0.001f) {
                            float r_final = (r_f + r_b * (1.0f - a_f) * a_b) / a_final;
                            float g_final = (g_f + g_b * (1.0f - a_f) * a_b) / a_final;
                            float b_final = (b_f + b_b * (1.0f - a_f) * a_b) / a_final;
                            
                            // 高亮截断饱和限制，防止浮点数在 HDR 合成时溢出 1.0 导致 uint8_t 环绕回零产生黑白条带（黑白相间的圈圈/斑马纹）走样
                            if (r_final > 1.0f) r_final = 1.0f;
                            if (g_final > 1.0f) g_final = 1.0f;
                            if (b_final > 1.0f) b_final = 1.0f;
                            
                            buffer[idx_rgba]     = (uint8_t)(r_final * 255.0f);
                            buffer[idx_rgba + 1] = (uint8_t)(g_final * 255.0f);
                            buffer[idx_rgba + 2] = (uint8_t)(b_final * 255.0f);
                            buffer[idx_rgba + 3] = (uint8_t)(a_final * 255.0f);
                        }
                    } else {
                        // 仅后表面可见
                        buffer[idx_rgba]     = (uint8_t)(buffer_back[idx_rgba] * 0.7f);
                        buffer[idx_rgba + 1] = (uint8_t)(buffer_back[idx_rgba + 1] * 0.7f);
                        buffer[idx_rgba + 2] = (uint8_t)(buffer_back[idx_rgba + 2] * 0.7f);
                        buffer[idx_rgba + 3] = (uint8_t)(buffer_back[idx_rgba + 3] * 0.7f);
                    }
                }
            }
        }

        // ==============================================================
        // ⚡ 终极图形学优化：双通道自适应物理 Alpha 抗锯齿 (Dual-Pass Alpha Edge-AA)
        // ==============================================================
        // 通过真正的 Alpha 通道物理混合来消除边缘锯齿，彻底根治边缘发暗/黑边/奇怪灰边问题。
        // 第一通道：平滑边缘前景像素本身的透明度，使其与背景产生平滑过渡。
        // 第二通道：将前景像素的明亮色彩和渐变透明度自适应向外羽化扩散，利用 Alpha 物理透明度
        //          与终端真实背景（不论是黑、灰还是透明）进行高保真融合，绝不画任何死板的暗色像素。
        // ==============================================================
        uint8_t *temp_buffer = malloc(BUFFER_SIZE);
        memcpy(temp_buffer, buffer, BUFFER_SIZE);

        // 第一通道：平滑边缘前景像素本身的透明度
        for (int y = 1; y < HEIGHT - 1; y++) {
            for (int x = 1; x < WIDTH - 1; x++) {
                int idx = y * WIDTH + x;
                int idx_rgba = idx * 4;
                
                if (temp_buffer[idx_rgba + 3] == 255) {
                    // 检测 4 邻域背景像素数量
                    int bg_count = 0;
                    if (temp_buffer[((y - 1) * WIDTH + x) * 4 + 3] == 0) bg_count++;
                    if (temp_buffer[((y + 1) * WIDTH + x) * 4 + 3] == 0) bg_count++;
                    if (temp_buffer[(y * WIDTH + x - 1) * 4 + 3] == 0) bg_count++;
                    if (temp_buffer[(y * WIDTH + x + 1) * 4 + 3] == 0) bg_count++;
                    
                    if (bg_count > 0) {
                        // 边缘前景像素：根据背景邻居数量降低 alpha，使其最外层边缘产生柔和的物理通透感
                        // bg_count = 1 -> alpha = 195 (柔和过渡)
                        // bg_count = 2 -> alpha = 145 (较强透明)
                        // bg_count >= 3 -> alpha = 95  (极高透明，用于细小尖端)
                        int new_alpha = 255 - bg_count * 50;
                        if (new_alpha < 85) new_alpha = 85;
                        buffer[idx_rgba + 3] = new_alpha;
                    }
                }
            }
        }

        // 第二通道：向外羽化扩散，计算背景像素的混合色彩和自适应 Alpha
        for (int y = 1; y < HEIGHT - 1; y++) {
            for (int x = 1; x < WIDTH - 1; x++) {
                int idx = y * WIDTH + x;
                int idx_rgba = idx * 4;
                
                // 仅处理原始透明背景像素
                if (temp_buffer[idx_rgba + 3] == 0) {
                    int fg_count = 0;
                    int sum_r = 0, sum_g = 0, sum_b = 0;
                    
                    int neighbors[4] = {
                        ((y - 1) * WIDTH + x) * 4,
                        ((y + 1) * WIDTH + x) * 4,
                        (y * WIDTH + x - 1) * 4,
                        (y * WIDTH + x + 1) * 4
                    };
                    
                    for (int i = 0; i < 4; i++) {
                        int n_rgba = neighbors[i];
                        if (temp_buffer[n_rgba + 3] == 255) {
                            fg_count++;
                            sum_r += temp_buffer[n_rgba];
                            sum_g += temp_buffer[n_rgba + 1];
                            sum_b += temp_buffer[n_rgba + 2];
                        }
                    }
                    
                    if (fg_count > 0) {
                        // 这是一个与甜甜圈相邻的背景像素
                        // 它的颜色设为邻近前景像素的平均色彩（保持高保真高亮度，绝不发暗！）
                        buffer[idx_rgba]     = sum_r / fg_count;
                        buffer[idx_rgba + 1] = sum_g / fg_count;
                        buffer[idx_rgba + 2] = sum_b / fg_count;
                        
                        // 它的 Alpha 根据邻近前景像素数量自适应计算，实现物理覆盖率抗锯齿
                        // fg_count = 1 -> alpha = 65 (25% 覆盖度)
                        // fg_count = 2 -> alpha = 120 (47% 覆盖度)
                        // fg_count = 3 -> alpha = 175 (68% 覆盖度)
                        // fg_count >= 4 -> alpha = 220 (86% 覆盖度)
                        int new_alpha = fg_count * 55 + 10;
                        if (new_alpha > 220) new_alpha = 220;
                        buffer[idx_rgba + 3] = new_alpha;
                    }
                }
            }
        }
        free(temp_buffer);

        // 7. C 语言亚毫秒级无损 PNG 编码
        size_t png_len = 0;
        uint8_t *png_data = encode_png(buffer, WIDTH, HEIGHT, &png_len);

        // 8. 写入终端并请求 GPU 渲染
        printf("\033[%d;%dH", start_row, start_col);
        send_image_via_kitty(png_data, png_len, target_cols, target_rows);
        free(png_data);

        // 8b. 在画面下方居中输出控制提示与当前状态，并清空当前行以防乱码
        printf("\033[%d;%dH\033[K", start_row + target_rows + 1, start_col);
        if (material_mode == 0) {
            printf("\033[1;36m🎨 当前材质: 电影级黏土 (Clay) \033[0;32m| [S] 键切换材质 | [Q] 键安全退出\033[0m");
        } else {
            printf("\033[1;35m💎 当前材质: 水晶玻璃 (Glass) \033[0;32m| [S] 键切换材质 | [Q] 键安全退出\033[0m");
        }

        // 9. 自动增量角度 (60 FPS 精准阻尼流速，旋转平滑流畅)
        angle_x += 0.025f;
        angle_y += 0.015f;
        angle_z += 0.010f;

        // 10. 精准锁帧：排除计算工作时间耗时，物理锁定 60 FPS
        struct timespec frame_end;
        clock_gettime(CLOCK_MONOTONIC, &frame_end);
        double elapsed = (frame_end.tv_sec - frame_start.tv_sec) + 
                         (frame_end.tv_nsec - frame_start.tv_nsec) / 1e9;
        double sleep_needed = FRAME_DURATION - elapsed;

        if (sleep_needed > 0) {
            struct timespec req = {
                .tv_sec = (time_t)sleep_needed,
                .tv_nsec = (long)((sleep_needed - (time_t)sleep_needed) * 1e9)
            };
            nanosleep(&req, NULL);
        }
    }

    // 退出还原终端
    tcsetattr(STDIN_FILENO, TCSANOW, &old_settings);
    printf("\033_Ga=d,i=2\033\\\033[?25h\033[2J\033[H");
    fflush(stdout);

    free(buffer);
    free(z_buffer);
    free(buffer_back);
    free(z_buffer_back);
    printf("💡 3D 实体/水晶玻璃甜甜圈演示已安全退出，终端属性还原成功。\n");
    return 0;
}
