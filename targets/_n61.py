# -*- coding: utf-8 -*-
"""N61 设备、引导器和工具配置。

N61AP = iPhone 6 (iPhone7,2)，A8/t7000。与 N56AP（iPhone 6 Plus）同 SoC、同 16H88
基线，但板级配置不同：1334×750 屏、摄像头无 OIS、电池更小、DeviceTree 节点与
机型文件不同。

标 TODO 的字段必须用 n61 自己的 SystemA / 12.5.8 固件核实后再填，不要照抄 N56。
"""

from targets._n56 import TOOLS  # noqa: F401  工具链与 N56 相同

DEVICE = {
    'model': 'n61ap',
    'product': 'iPhone7,2',
    'ecid': '',
    'udid': '',
    # TODO: 用 n61 12.5.8 内核里的 PMU 驱动与寄存器表核实（N56 为 d2186）
    'pmu': 'd2186',
    # TODO: 用 SystemA 的 AppleMultitouchSPIN61 personality 核实
    'touch': 'multi-touch,n61',
    # TODO: 用 n61 内核/DT 核实，勿直接沿用 N56
    'codec': 'CS42L67',
    'charger': 'SN2400',
    'memory': {'base': 0x800000000, 'size': 0x40000000},
    'display': {'width': 1334, 'height': 750, 'scale': 2},
}
