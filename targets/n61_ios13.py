# -*- coding: utf-8 -*-
"""iPhone 6 (N61AP) × iOS 13.7：目标清单骨架。

⚠ 骨架状态，未在实机验证，非 --dry-run 实跑会被入口拦下。
  移植步骤、缺口和验证顺序见 docs/porting/N61AP.md。

与 targets/n56_ios13.py 的差异只写了确定的几处：
  - 设备常量换成 n61；
  - 原机 SystemA 的 IPSW 换成 4.7 吋 12.5.8（同为 16H88）；
  - derived 目录换成 n61ap_ios12 前缀。

其余常量（卷布局、boot-args、features、启动链顺序）沿用 N56 的取值：
它们描述的是"iOS 13.7 第二系统"这条路线，不是机型本身。等 n61 实机跑通后再逐项确认。
"""

from copy import deepcopy
from targets._n61 import DEVICE, TOOLS

TARGET = {
    "name": "n61-ios13",
    "version": "ios13",
    "os_version": "13.7",
    "source_root": "donors",

    # 移植状态：scaffold = 只有常量骨架，构建链尚未接到 n61 原生输入
    "porting_status": "scaffold",
    "porting_note": "见 docs/porting/N61AP.md：extract_ipsw/paths/inputs 仍是 N56 硬编码",

    # ===================== 设备级常量（跨 iOS 版本不变）=====================
    "device": deepcopy(DEVICE),

    # 第二系统根分区号：s4。kairos 把 iBEC 的 root-matching 改成 disk0s1s4。
    "root_part": 4,
    # 卷布局：建 s4=SystemB / s5=DataB（role 0），最后改 role。
    "volumes": {
        "create": ["SystemB", "DataB"],
        "roles": {3: 0x80, 4: 0x1, 5: 0x40},     # s4=System, s5=Data（0x1/0x40 在容器内唯一）
    },
    # 第二系统 Data 默认启用内容保护。
    "data_protection": "encrypted",
    "mounts": {"system_b": 4, "data_b": 5, "system12": 1},   # device slices mounted at /mnt6, /mnt7, /mnt1

    "ramdisk_port": 2222,
    "ramdisk_password": "alpine",
    "ramdisk_dir": "tools/SSHRD_Script/sshramdisk",       # iOS12.5.8 SSHRD 镜像

    # ===================== 版本级常量（随 iOS 版本变）=====================
    # 成功启动链的 boot-args（debug=0x2014e、amfi/cs 放行、root=disk0s1s4）；n61 待实测
    "bootargs": "rd=disk0s1s4 -v amfi_get_out_of_my_way=1 "
                "cs_enforcement_disable=1 wdt=-1 debug=0x2014e",
    "source_profiles": {
        # 键名 n56 在现有代码里表示"原机 SystemA"，移植时保留键名、换内容。
        "n56": {"build": "16H88", "board": "n61ap",
                "ipsw": "iPhone_4.7_12.5.8_16H88_Restore.ipsw"},
        "n66": {"build": "17H35", "rootfs_entry": "038-68134-036.dmg",
                "ipsw": "iPhone_5.5_13.7_17H35_Restore.ipsw"},
        "j96": {"build": "17H35", "rootfs_entry": "038-68261-036.dmg",
                "ipsw": "iPad_64bit_TouchID_13.7_17H35_Restore.ipsw"},
    },

    # ===================== 工具链（仓库 tools/）=====================
    "tools": deepcopy(TOOLS),

    # ===================== donor 源（本地 donors/）=====================
    "donors": {
        "apfs14": "projects/dualra1n-bin/apfsios14",              # iOS14 的 fsck + apfs.fs
        "sys12_mount_hint": "disk0s1s1",   # SEP 固件 / 机型文件来源（s1 只读挂）
    },

    # ===================== 从 IPSW 生成（ipsw/cache/derived）=====================
    # TODO: 这些路径要等 tools/extract_ipsw.py 支持 n61 profile 后才会被生成
    "derived": {
        "ibss_src": "extracted/n61ap_ios12/iBSS.n61.patched",  # 首次需 DFU 解密
        "ibec_dec": "extracted/n61ap_ios12/iBEC.n61.dec",
        "j96_kernel": "extracted/j96ap_ios13/kernelcache.release.ipad5",
        "trustcache": "extracted/j96ap_ios13/038-68261-036.dmg.trustcache",
    },

    "full_trustcache": True,
    "trustcache_builder": "patches.ios13.impl.rootfs.trustcache",
    # TODO: 这些 cdhash 是 N56 构建产物的配套值，n61 构建后要整组替换
    "profile_cdhashes": [
        "ea9b6b492e5f1fc2e1692a0ec93c65ab594c20c4",  # bluetoothd.xpc13
        "e001b09ea59f73cc2804d1654059138ed571029a",  # BlueTool 16H88
        "f2a9b00a2e7fb8e0fefbccdf80bfc79a2aec2202",  # nanoregistryd
        "2f4f85f4bdd0937195536da3d89927dfd01b142f",  # nanoregistrylaunchd
        "44b3dce9c846916db1419304401ceabe9b872031",  # fairplayd.H2
        "eff0e0b43afd6e72cfd81fda04325ce4282d9824",  # healthappd
    ],

    # ===================== patch 选挂 =====================
    # base：每层（dt/kc）选且仅选一个。
    "bases": {
        "dt": "dt.base",
        "kc": "kc.j96_clean",
    },
    # Features select the default full build; --patches overrides KC alone.
    "features": [
        "pmu", "touch", "charging", "chestnut", "wifi", "vibration", "audio",
        "core",       # rootfs 流写 + finish + 改 role + 机型文件（启动必备）
        "ui",         # 图标/键盘/控制中心/SpringBoard/设置 3× 图标
        "bluetooth",  # 12→13 蓝牙用户态
        "baseband",   # factorydata + CommCenter + Mav10 + Carrier Bundles
        "sep",        # SEP 固件（boot 必备）+ fairplayd.H2
        "health",     # 健康 App 框架 repair-v7
        "checkra1n",  # 离线 KPF、用户态工具与 USB SSH
        "touchid",    # Mesa ↔ iOS 12 SEP 收发桥
    ],
    # 显式追加的 patch id（不靠 feature）
    "patches": [],
    # 排除
    "exclude": [],

    # ===================== 启动链发送顺序 =====================
    # gaster pwn/reset → iBSS → iBEC → DT(devicetree) → TC(firmware) → KC → bootx
    "boot_chain": ["iBSS", "iBEC", "DeviceTree", "TrustCache", "KernelCache"],
}
