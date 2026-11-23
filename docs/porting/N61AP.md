# N61AP（iPhone 6）iOS 13.7 移植方案

> 状态：**方案 + 骨架，未在实机验证**。本分支只包含能离线完成的部分：
> 设备常量、目标清单骨架和这份改动清单。任何可启动产物都必须等真机和 macOS 就绪后生成。

## 0. 来源

B 站 [BV14bst6WEwP](https://www.bilibili.com/video/BV14bst6WEwP)：iPhone 6（A1586，12.5.8 16H88）
以第二系统方式启动 iOS 13.7，作者说明"基于 n56-patcher 修改，添加 n61ap 支持，已知无基带"。

## 1. 为什么不能只换机型名

n56-patcher 里大量常量不是"配置"，而是从 N56 真机数据里量出来的：

- 内核与 DeviceTree 取自 N56 自己的 12.5.8（16H88）固件，IM4P 解密要用设备的 GID 密钥；
- PMU/GPIO 的寄存器值与掩码来自 N56 的 SystemA；
- 触摸 personality、机型文件、热管理模型、Wi-Fi/基带固件也都按 N56 的目录/型号取值。

N61 与 N56 同为 A8（t7000）、同为 16H88，管线可以复用，但**原生输入层必须整体换成 n61 的**。
两者板级差异至少包括：1334×750 屏（N56 是 1920×1080）、摄像头无 OIS、电池容量、
DeviceTree 的 board/display/battery 节点、机型文件（A1586/A1549 vs A1522/A1524）。

## 2. 必须从 n61 侧取得的输入

| 输入 | 来源 | 用途 | 现有代码位置 |
| --- | --- | --- | --- |
| iBSS / iBEC | 4.7 吋 12.5.8 IPSW，DFU 下 `gaster decrypt` | 启动链 | `tools/extract_ipsw.decrypt_iboot` |
| `DeviceTree.n61ap` | 同一 IPSW，`img4` 解 im4p → `devicetree-parse` | DT 基底 | `tools/extract_ipsw.generate` |
| `kernelcache.release.iphone7` | 同一 IPSW（成员名需按 BuildManifest 核实） | KC 基底 / 硬件适配 | `patches/shared/impl/paths.py`（`N56` 常量） |
| 机型文件 | 设备 SystemA | jetsam / mtprops / audio / MediaToolbox / ACTFramework | `patches/shared/rootfs/n56_model_files.py` |
| 热管理 bundle | SystemA `ThermalMonitor.bundle/N61AP.bundle` | 休眠/温度模型 | `patches/shared/impl/rootfs/thermal/*` |
| 监管认证图 | SystemA `RegulatoryImages`，A1586/A1549 | 设置里的认证信息 | 同上 |
| Wi-Fi 固件 | SystemA `usr/share/firmware/wifi/…`（芯片型号需核实） | Wi-Fi 用户态 | `patches/shared/impl/kc/wifi/*` |
| 基带固件 + CommCenter 产品表 | SystemA + dyld cache | 基带（视频里未完成） | `patches/ios13/impl/rootfs/baseband_firmware.py` |

## 3. 代码改动清单

按依赖顺序，前四项是"让 n61 能构建"，后四项是"让 n61 能开机"。

1. `tools/extract_ipsw.py`
   - 顶部的 `N56` / `N56_ROOTFS` / `WIFI` 与 `generate()` 里的成员名全部硬编码。
   - 需要改为按 target 的 profile 取：board（`n61ap`）、IPSW 文件名、kernel/DT 成员、
     rootfs DMG 条目（4.7 吋与 5.5 吋的 `038-…dmg` 不同）、Wi-Fi 目录。
   - 建议直接解析 `BuildManifest.plist` 的 BuildIdentities，按 `DeviceClass` 取
     `KernelCache` / `DeviceTree` / `OS`，与 `patches/shared/impl/inputs.py` 的做法一致。
2. `patches/shared/impl/paths.py`
   - `N56` 常量指向 `extracted/n56ap_ios12/...`；应改为由目标注入或按设备 profile 解析。
3. `patches/shared/impl/inputs.py`
   - `extract(archive, "n56ap", "16H88", …)` 与 `archives["n56"]` 同问题。
4. `targets/_n61.py` + `targets/n61_ios13.py`
   - 本分支已加骨架；`source_profiles` 的 `n56` 键在移植后语义是"原机 SystemA"，
     为兼容现有代码暂时保留键名。
5. `patches/shared/impl/dt/dt_patch.py`
   - 基底树换成 `DeviceTree.n61ap.jsonc`；`n56_platform.py` 里的 DRAM/GPIO/DART/NVRAM
     数值、NFC schema、display/battery 节点都要按 n61 的 DT 重新对。
6. `patches/shared/impl/kc/pmu_d2186.py`
   - LDO 表、mapper、两处 GPIO 修正（`0xfffffff006da049c` / `0xfffffff006da04d0`）都是
     N56 实测值。SoC 相同、MMIO 地址大概率相同，但**取值不能照抄**，要按 n61 SystemA 核对。
7. 触摸 / 音频 / 振动 / 相机
   - `kc/n56_touch.py` 的 personality 名、`apple_mt` 参数；
     `Library/Audio/Tunings/N61`、`MediaToolbox/N61`、ACTFramework 等资源路径。
8. `patches/shared/rootfs/n56_model_files.py`
   - 路径里的 `N56` → `N61`；`N56AP.bundle` → `N61AP.bundle`；
     监管图 variant 的 `A1522/A1524` → `A1586/A1549`（先确认两型号各对应哪张图）。

## 4. 建议里程碑

| 级别 | 目标 | 验证方式 |
| --- | --- | --- |
| M0 | `init` 能从 4.7 吋 IPSW 产出 n61 的 kernel/DT | 与设备 SystemA 的 DT 节点逐项 diff |
| M1 | DT 构建通过 | 发送 DT 能过 iBoot 校验 |
| M2 | KC 构建通过 | 内核能起、串口有输出 |
| M3 | 建卷 + 写系统 | ramdisk 内检查卷 role / 空间 |
| M4 | 首次进桌面 | 视频作者的进度 |
| M5 | 显示 / 触屏参数对齐 | 分辨率、触摸坐标、亮度 |
| M6 | Wi-Fi | 扫描、关联、AWDL |
| M7 | 基带 | CommCenter 识别 N61、Mav10 固件 |
| M8 | 传感器 / 相机 / 音频 / 健康 | 逐项对照 N56 的验收表 |

## 5. 已知坑

- **IM4M 每次刷机都会变**，旧启动包同时作废；TrustCache 必须和同一次构建的 mrm/rootfs 成套。
- 16 GB 机型空间紧张（视频里是 A1586，容量按实机确认）。
- 不要把 N56 的 PMU/GPIO 数值当默认值：地址相同不代表取值相同，错了表现为不开机或外设全挂。
- Wi-Fi/基带固件必须与 12.5.8 的版本配套，混用会出现"能开机但无线全无"。
- 监管图按物理型号选，SettingsFoundation 的 fallback 是 variant A。
- 视频里的"无基带"说明 M7 未完成，不要拿它当验收标准。

## 6. 本分支包含 / 不包含

包含：

- `targets/_n61.py`：n61 设备常量（未核实的字段标了 TODO）；
- `targets/n61_ios13.py`：目标清单骨架，`porting_status = "scaffold"`，
  非 `--dry-run` 实跑会被入口显式拦下并指向本文档；
- 本文档。

不包含：`extract_ipsw` 的 profile 化、任何 DT/KC 补丁常量、可启动产物。
这些都需要真机数据，离线写出来只会是"看起来能跑"的假移植。

## 7. 设备就绪后的第一步

```sh
# ipsw/ 下放好三个包（第三个换 4.7 吋的）
#   iPhone_4.7_12.5.8_16H88_Restore.ipsw      # n61 原生
#   iPhone_5.5_13.7_17H35_Restore.ipsw        # n66 donor
#   iPad_64bit_TouchID_13.7_17H35_Restore.ipsw # j96 donor
python3 tools/extract_ipsw.py --n56-ipsw ipsw/iPhone_4.7_12.5.8_16H88_Restore.ipsw
```

先确认提取出的 `DeviceTree.n61ap.jsonc` 与 `kernelcache` 能被现有解析脚本读通，
再动第 3 节的第 1～3 项；否则后面的构建全部无从谈起。
