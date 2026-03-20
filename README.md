# Anich Flatpak Packaging

Anich 的 Flatpak 打包配置文件。

## 应用信息

| 项目 | 值 |
|------|-----|
| 名称 | Anich |
| 版本 | 1.5.8 |
| App ID | org.eu.emmmm.anich |
| Runtime | org.gnome.Platform 49 |
| 官网 | https://anich.emmmm.eu.org |
| 源码 | https://github.com/Sle2p/AniCh |

## 安装

### 方式一：本地构建

```bash
# 安装依赖
sudo dnf install flatpak flatpak-builder  # Fedora
# 或
sudo apt install flatpak flatpak-builder  # Debian/Ubuntu

# 添加 Flathub 仓库
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# 安装 GNOME SDK
flatpak install flathub org.gnome.Platform//49 org.gnome.Sdk//49

# 克隆仓库
git clone https://github.com/你的用户名/仓库名.git
cd 仓库名

# 构建并安装
flatpak-builder --user --install --force-clean build-dir org.eu.emmmm.anich.yml
```

### 方式二：从本地安装（如果有 .flatpak 文件）

```bash
flatpak install --user org.eu.emmmm.anich.flatpak
```

## 运行

```bash
flatpak run org.eu.emmmm.anich
```

## 卸载

```bash
flatpak uninstall org.eu.emmmm.anich
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `org.eu.emmmm.anich.yml` | Flatpak manifest 构建配置 |
| `org.eu.emmmm.anich.desktop` | 桌面入口文件 |
| `org.eu.emmmm.anich.metainfo.xml` | 应用元数据 |
| `org.eu.emmmm.anich.png` | 应用图标 (512x512) |
| `flathub.json` | Flathub 构建配置 |

## 权限说明

| 权限 | 用途 |
|------|------|
| `--share=network` | 网络访问（在线视频、弹幕） |
| `--device=dri` | GPU 硬件加速 |
| `--socket=pulseaudio` | 音频播放 |
| `--socket=wayland` | Wayland 支持 |
| `--socket=fallback-x11` | X11 后备 |
| `--talk-name=org.gnome.SessionManager` | 防止熄屏 |
| `--persist=anich_data` | 数据持久化 |

## 许可证

- 本打包配置：CC0-1.0
- Anich 应用：Proprietary

## 相关链接

- [Anich 官网](https://anich.emmmm.eu.org)
- [Anich GitHub](https://github.com/Sle2p/AniCh)
- [Flathub](https://flathub.org)