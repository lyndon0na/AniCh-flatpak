# AniCh Flatpak 打包

将官方 Linux `.deb` 重新打包为 Flatpak 的构建配置。

[English](README.md) | **简体中文** | [打包说明](docs/packaging-notes.md)

当前版本（1.5.27）已发布，一条命令即可安装：

```sh
flatpak install --user https://lyndon0na.github.io/AniCh-flatpak/org.eu.emmmm.anich.flatpakref
```

## 应用信息

| 项目 | 值 |
|------|-----|
| 名称 | AniCh |
| 版本 | 1.5.27 |
| App ID | `org.eu.emmmm.anich` |
| Runtime | `org.gnome.Platform` 51 |
| 架构 | x86_64 |
| 上游源码 | https://github.com/Sle2p/AniCh |
| 官网 | https://anich.emmmm.eu.org |
| 应用载荷 | 上游的 `anich-linux-1.5.27.deb`，以 [extra-data](https://docs.flatpak.org/en/latest/module-sources.html#extra-data) 方式声明：flatpak 在安装该应用的机器上下载它、校验 sha256，再由 `apply_extra` 解包 |

## 安装

### 从仓库安装

```sh
flatpak install --user https://lyndon0na.github.io/AniCh-flatpak/org.eu.emmmm.anich.flatpakref
```

该命令会同时添加远程仓库，之后的版本通过 `flatpak update`（或桌面软件中心）更新。安装时会从 GitHub 下载约 22 MB 的 `.deb`，应用本体就来自那里。

### 本地构建

```sh
# 安装依赖
sudo dnf install flatpak flatpak-builder      # Fedora
sudo apt install flatpak flatpak-builder      # Debian / Ubuntu

# 添加 Flathub，并安装 GNOME runtime 与 SDK
flatpak remote-add --if-not-exists --user flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --user flathub org.gnome.Platform//51 org.gnome.Sdk//51

# 克隆并构建
git clone https://github.com/lyndon0na/AniCh-flatpak.git
cd AniCh-flatpak
flatpak-builder --user --install --force-clean --repo=repo build org.eu.emmmm.anich.yml
```

构建时不需要 `.deb`：它是 extra-data 源，构建只用到 runtime 和 SDK。`.deb` 在安装应用的机器上从上游 release URL 拉取，并按 manifest 中记录的 sha256 校验。

### 为什么没有 bundle

bundle 无法携带 extra-data 记录：它存放在 commit 的 detached metadata 里，而 `flatpak build-bundle` 不会包含它，所以安装 bundle 会报 `Extra data missing in detached metadata`。因此发布在 GitHub Pages 上的仓库是唯一的安装途径。

## 运行

```sh
flatpak run org.eu.emmmm.anich
```

## 卸载

```sh
flatpak uninstall --user org.eu.emmmm.anich
```

flatpak 会询问是否一并删除 `~/.var/app/org.eu.emmmm.anich/` 中的应用数据。

## 权限说明

| 权限 | 用途 |
|------|------|
| `--share=network` | 在线番剧源、弹幕 API 与 DoH 解析 |
| `--share=ipc` | X11 后备路径所需的共享内存 |
| `--socket=wayland` | Wayland 支持 |
| `--socket=fallback-x11` | X11 后备 |
| `--socket=pulseaudio` | 音频播放 |
| `--device=dri` | GPU 渲染与 VA-API 硬解 |
| `--talk-name=org.freedesktop.ScreenSaver` | 播放时阻止熄屏与休眠 |
| `--talk-name=org.freedesktop.Notifications` | 下载与播放通知 |

不申请任何宿主文件系统权限。应用默认写入的所有内容——下载的媒体、缓存、首次运行时复制的 Anime4K 着色器以及数据库——都位于 `~/.var/app/org.eu.emmmm.anich/`，沙箱本身就会提供。若要让应用访问真实路径，需要额外授权：文件选择器可以显示 `~/Videos`，但在授权之前应用无法读写它。

```sh
flatpak override --user --filesystem=xdg-download org.eu.emmmm.anich
```

若需整个家目录，可改用 `--filesystem=home`，或在 Flatseal 中按应用设置。

## 文件说明

| 文件 | 说明 |
|------|------|
| `org.eu.emmmm.anich.yml` | Flatpak manifest（GNOME runtime 51） |
| `apply_extra` | 安装与更新时运行：解包 `.deb` |
| `extract-deb.py` | 解析 `.deb` 的 ar 容器并解出 `data.tar.zst`，由 `apply_extra` 调用 |
| `anich-wrapper` | `/app/bin/anich` 入口 |
| `org.eu.emmmm.anich.desktop` | 桌面入口文件 |
| `org.eu.emmmm.anich.metainfo.xml` | AppStream 元数据 |
| `icons/org.eu.emmmm.anich-*.png` | 安装的图标（128 / 256 / 512） |
| `org.eu.emmmm.anich.flatpakref.in` | 一行安装用的模板，由 CI 填充并发布 |
| `org.eu.emmmm.anich.flatpakrepo.in` | 手动添加远程仓库用的模板 |
| `.github/workflows/build.yml` | CI：构建、校验、发布仓库与 release |
| `.github/workflows/upstream.yml` | 每日检查上游，自动开升级 PR |
| `docs/` | [打包说明](docs/packaging-notes.md) |
| `LICENSE` | CC0-1.0（仅打包配置；应用本身为专有软件） |

## CI

`.github/workflows/build.yml`：

* 推送到 `main` 或手动触发构建、安装并校验部署后的目录树；
* `v*` 标签额外对构建签名、更新已发布的仓库并创建 GitHub release；
* `.github/workflows/upstream.yml` 每天运行：当 Sle2p/AniCh 发布新版本时，会开一个把 manifest 指向新版本的 PR。合并 PR 不会发布任何东西——发布靠打标签。

runner 没有显示器，所以 GUI 冒烟测试在 Xvfb 下运行，属于尽力而为的步骤，只报告不使构建失败；结构性检查则会使构建失败。

```sh
git tag v1.5.27
git push origin v1.5.27
```

## 发布

打标签会发布仓库，这需要一次性配置几项：

1. **`GPG_PRIVATE_KEY`** 仓库 secret：签名密钥的 ASCII-armored 私钥。CI 从中推导 key id 与公钥，对 commit 和仓库摘要签名，并把公钥写入描述文件。
2. **GitHub Pages** 服务于 `gh-pages` 分支（Settings → Pages → Source）。每次打标签会把 OSTree 仓库、`org.eu.emmmm.anich.flatpakref`、`org.eu.emmmm.anich.flatpakrepo` 和一个图标推送到该分支。
3. **允许来自 Actions 的 PR**（Settings → Actions → General → Workflow permissions），否则每日上游检查无法开升级 PR。

发布新版本时，修改 manifest 中的 `url`、`sha256`、`size`（以及 metainfo 里的 `<release>` 条目），提交并打标签即可。

与 JVM 或 CEF 应用不同，这里的载荷只有约 22 MB，因此发布一个新 commit 成本很低。但 flatpak 只要 commit 变化就会重新下载并重新应用 extra data，即使 extra-data 记录没变，所以无关改动仍建议合并到同一个标签里。

仓库里的描述文件是模板：`@PAGES_URL@` 与 `@GPGKEY@` 在发布时才替换，因此仓库中不含任何密钥材料。

## 说明

* 这是**非官方**打包。上游并不支持，请在本仓库反馈问题。
* 应用在安装或更新时从 GitHub 下载，不由本仓库分发。若上游删除某个 release 资产，新安装会失败，直到把 manifest 中的 sha256 指向新资产。
* 应用数据位于 `~/.var/app/org.eu.emmmm.anich/`，与系统安装的 AniCh 完全隔离。

## 许可证

应用与图标美术来自 [Sle2p/AniCh](https://github.com/Sle2p/AniCh)，为专有软件。本仓库仅提供打包配置，以 [CC0-1.0](LICENSE) 发布。

## 相关链接

* [AniCh 官网](https://anich.emmmm.eu.org)
* [AniCh 源码](https://github.com/Sle2p/AniCh)
* [打包说明](docs/packaging-notes.md)
* [安装页面](https://lyndon0na.github.io/AniCh-flatpak/)
* [Releases](../../releases)
