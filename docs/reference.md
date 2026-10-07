# 参数参考

## 方案 JSON

方案可以通过网页保存，也可以直接编写并使用 `--config` 传入 CLI。所有长度单位为毫米，颜色使用六位十六进制值。

```json
{
  "notes": "F Gb G Ab A Bb B C1",
  "offsets": [0, 0, 0.1, 0, 0, 0, 0, -0.1],
  "extension": 0,
  "colors": {
    "front": "#538d82",
    "back": "#c4cfbe",
    "clip": "#c98c53"
  },
  "layers": [{
    "kind": "text",
    "text": "LILT",
    "target": "back",
    "mode": "inlay",
    "color": "#b65c2f",
    "x": 0,
    "y": 40,
    "width": 18,
    "rotation": 0,
    "depth": 0.4
  }]
}
```

| 字段 | 含义 |
| --- | --- |
| `notes` | 音符序列，可使用字符串或标签数组；包含停顿时仍须满足 8–33 个位置。 |
| `offsets` | 按序列顺序排列的齿根位置增量，范围 −2 至 2 mm；缺省项为 0。正值缩短自由振动段，与网页“自由长度增量”的符号相反。 |
| `extension` | 整体自由齿长增量，范围 −5 至 10 mm，默认 0；同时改变框架深度。 |
| `colors` | `front`、`back`、`clip` 分别指定前板、背板和固定夹颜色。 |
| `layers` | 图文图层，最多 12 层。 |

## 图文图层

| 字段 | 取值或含义 |
| --- | --- |
| `kind` | `text`、`svg` 或 `image`。 |
| `text` | 文字内容，长度为 1–80 个字符。 |
| `file` | SVG 或图片路径，相对路径以 CLI 当前工作目录为准。 |
| `target` | `front`、`back` 或 `both`；默认 `back`。 |
| `mode` | `engrave`（凹刻）、`emboss`（凸起）或 `inlay`（平齐嵌色）；默认 `engrave`。 |
| `x`、`y` | 外侧底面的图案中心位置，X 向右、Y 向下；默认 `(0, 40)`。 |
| `width` | 图案宽度，范围 1–100 mm，默认 18；高度按原图比例计算。 |
| `rotation` | 旋转角度，范围 −360 至 360°，默认 0。 |
| `depth` | 凹刻、嵌色深度或凸起高度，范围 0.1–1.5 mm，默认 0.4。 |
| `color` | 文字、位图或单色 SVG 的颜色。 |
| `preserveColors` | 是否保留 SVG 的原始配色，默认 `true`。 |
| `threshold` | 位图转轮廓阈值，默认 128。 |
| `invert` | 是否反相位图轮廓，默认 `false`。 |

图文会裁切到面板实体范围。深度超过局部厚度可能切穿面板，应结合 3D 预览检查位置与深度。SVG 和图片文件上限为 5 MB，SVG 最多支持 16 种纯色。

SVG 保留填充区域、孔洞和遮挡顺序。位图将深色区域转换为几何轮廓，通过阈值和反相选择区域。文字使用本机字体生成轮廓：优先读取 macOS 的 `/Library/Fonts/Arial Unicode.ttf`，其次读取 Linux 的 `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`，最后使用 Pillow 默认字体。当前没有字体选择参数，其他字体需在 `comb/artwork.py` 的 `text_geometry` 中指定。

CLI 输出的方案嵌入已生成轮廓，可复现当前模型。网页保存的方案还保留导入图像数据，可继续调整位图阈值。

## 平齐多色嵌色

`inlay` 在面板内部划分独立材料区域，外侧表面保持平齐。3MF 将面板底色与图案色块作为同一零件的组件保存，在切片软件中将各区域对应到实际耗材。STL 合并材料区域，无法保留平齐图案的颜色。

SVG 可在网页中保留原始配色并逐色修改，也可切换为单一图案颜色。使用相同颜色的区域可分配同一种耗材。

## OpenSCAD 参数

导出的 SCAD 嵌入基础框架网格与当前图文轮廓，可独立打开。常用参数如下：

| 参数 | 用途 |
| --- | --- |
| `notes`、`offsets`、`extension` | 音符、逐齿齿根调整和整体齿长。 |
| `front_color`、`back_color`、`clip_color` | 三个零件的预览颜色。 |
| `part` | 选择输出零件或摆盘。 |
| `baked_art` | 已嵌入图层的面板、位置、宽度、旋转、深度和方式；将对应项的宽度设为 0 可隐藏该层。 |
| `art_colors` | 已嵌入图层的色块颜色。 |
| `extra_text`、`extra_svg` | 新增文字或导入外部 SVG。 |
| `extra_target`、`extra_x`、`extra_y`、`extra_width` | 新增图文的目标面板、位置和宽度。 |
| `extra_color` | 新增图文的颜色。 |

`extra_svg` 使用相邻文件或绝对路径，该 SVG 文件需与 SCAD 一起保留。音符数量变化时，框架宽度自动调整。
