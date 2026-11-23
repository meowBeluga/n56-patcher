# n61-patcher（N61AP / iPhone 6）

**把 [n56-patcher](https://github.com/CelestialSayuki/n56-patcher) 的第二系统路线迁到 iPhone 6。**

简体中文 · [上游 README](README.md) · [移植方案](docs/porting/N61AP.md)

![Device](https://img.shields.io/badge/Device-iPhone%206-0A84FF?style=flat-square&logo=apple&logoColor=white)
![Status](https://img.shields.io/badge/Status-scaffold%20%2F%20untested-orange?style=flat-square)
![Target](https://img.shields.io/badge/Target-iOS%2013.7%20(17H35)-5E5CE6?style=flat-square)
![Host](https://img.shields.io/badge/Host-macOS%20%2B%20Xcode-30363D?style=flat-square)
![License](https://img.shields.io/badge/License-GPL--3.0-blue?style=flat-square)

> [!WARNING]
> **这个分支现在什么都装不了。** 它只有设备常量、目标清单骨架和一份方案文档，
> 不含任何可启动产物。把它当"能刷的系统"用，只会浪费时间，或者在真机上写坏分区。
>
> 目标清单带 `porting_status = "scaffold"`，除 `--dry-run` 外的实跑会被入口直接拒绝。

---

## 这是什么

[n56-patcher](https://github.com/CelestialSayuki/n56-patcher) 在 iPhone 6 Plus（iPhone7,1 / n56ap）
上把 iOS 13.7 / 14.8 / 15.8.8 作为第二系统装进同一台设备，硬件功能基本齐全。
本分支尝试把同一条路线搬到 **iPhone 6（iPhone7,2 / n61ap / A1586）**——也就是
[B 站 BV14bst6WEwP](https://www.bilibili.com/video/BV14bst6WEwP) 里演示的那件事。

和视频作者的做法一样：复用上游管线，只替换机型相关的那一层。

## 当前状态

| 部分 | 状态 | 说明 |
| --- | --- | --- |
| `targets/_n61.py` 设备常量 | 🟡 骨架 | 未核实字段已标 TODO |
| `targets/n61_ios13.py` 目标清单 | 🟡 骨架 | 卷布局 / boot-args / features 沿用 N56 取值 |
| `extract_ipsw` 的 n61 profile | ❌ 未做 | 仍硬编码 `n56ap` 与 5.5 吋 IPSW |
| `paths` / `inputs` 参数化 | ❌ 未做 | 仍指向 `n56ap_ios12` |
| DeviceTree 构建 | ❌ 未做 | 需要 n61ap 的原生 DT |
| KernelCache 构建 | ❌ 未做 | PMU / GPIO / 触摸常量都还是 N56 实测值 |
| 实机启动 | ❌ 未验证 | 无任何产物 |

一句话：**还没到能开机的阶段，离"能日常用"更远。**

## 为什么不能直接写

n61 的原生输入必须从真机取：

- iBSS / iBEC / DeviceTree / kernelcache 是 IM4P，解密要用设备的 GID 密钥，**必须 DFU**；
- PMU、GPIO、触摸 personality、机型文件、热管理模型、Wi-Fi/基带固件，都来自 n61 自己的 SystemA。

离线硬编码这些常量，得到的只会是"看起来能跑"的假移植。所以本分支把
"哪些是机械改动、哪些必须实测"分开列在 [docs/porting/N61AP.md](docs/porting/N61AP.md) 里，
而不是先写一堆猜出来的数。

## 现在能跑什么

先把依赖补齐（上游的子模块与工具，否则 `list` 会因缺 `DyldExtractor` 失败）：

```sh
git clone -b n61ap https://github.com/meowBeluga/n56-patcher.git
cd n56-patcher
bash tools/bootstrap.sh
```

然后只能做只读检查：

```sh
python3 n56patcher.py list --dry-run --target n61-ios13   # 只能 dry-run
python3 n56patcher.py status --target n61-ios13           # 会被骨架状态拦下
```

想跑上游的 N56 流程，请切回 `master` 并看 [上游 README](README.md)。

## 路线图

| 级别 | 目标 | 依赖 |
| --- | --- | --- |
| M0 | `init` 从 4.7 吋 12.5.8 IPSW 产出 n61 的 kernel / DT | 无（离线可做） |
| M1 | DT 构建并通过 iBoot 校验 | 真机 |
| M2 | KC 构建，内核能起 | 真机 |
| M3 | 建卷 + 写入系统 | 真机 + ramdisk |
| M4 | 首次进桌面（视频作者的进度） | 真机 |
| M5–M8 | 显示/触屏 → Wi-Fi → 基带 → 传感器/相机/音频 | 真机 |

M0 的代码改动（`extract_ipsw` 按 BuildManifest 取成员、`paths` / `inputs` 参数化）
不需要设备，是下一步要做的部分。

## 真机阶段的前置条件

- macOS + 完整 Xcode（iPhoneOS SDK）
- iPhone 6，A1586，当前为 iOS 12.5.8（16H88）
- 三份 IPSW：`iPhone_4.7_12.5.8_16H88`、`iPhone_5.5_13.7_17H35`、`iPad_64bit_TouchID_13.7_17H35`
- 至少 64 GB 空闲空间、能稳定传输数据的 Lightning 线
- **备份**：流程会建卷、写系统文件

## 安全与合规

- 本项目与 Apple 无关，按现状提供，**风险自负**；请先备份，别拿主力机试。
- 16 GB 机型空间非常紧，装第二系统前先看上游 iOS 14 文档的"空间"一节。
- 不包含 Apple 固件：`ipsw/`、`donors/`、`state/` 都在 `.gitignore` 里，请自行准备。
- 继承上游 **GPL-3.0**；修改和分发请保持同一许可证。

## 贡献

- 提 issue 请附完整报错和 `state/` 之外的环境信息；
- PR 需要真机验证证据（日志、串口输出、截图），纯静态改动请说明验证方式；
- 不要提交 IPSW、keybag、含 IMEI 的备份。

## 致谢

- [CelestialSayuki/n56-patcher](https://github.com/CelestialSayuki/n56-patcher)：整条管线与全部机型适配工作；
- checkra1n、SSHRD_Script、img4lib、devicetree-parse、gaster、dualra1n 等上游工具；
- B 站 [BV14bst6WEwP](https://www.bilibili.com/video/BV14bst6WEwP) 的作者，提供了 n61ap 可行的先例。
