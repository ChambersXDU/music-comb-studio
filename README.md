# LILT · 音乐梳子工坊

本机网页和 CLI 共用一套参数模型。输入实际音符名称，生成前板、背板和固定夹；图文放在零件的外侧底面；前板、背板和固定夹可以各自选择颜色。参考结构来自无文字、无钥匙孔 `notext.stl`，齿根尺寸按 F 至 C2 的 20 个音符还原。默认没有 TEST 字样，模型上的方向箭头保留。

![音乐梳子工坊](docs/images/studio.jpg)

## 打开网页

在 macOS 上双击 `启动音乐梳子.command`，然后访问 **http://127.0.0.1:8818**。首次启动会创建 Python 环境并安装依赖。窗口里的服务保持运行即可；按 Control-C 关闭服务。网页素材和 Three.js 都随项目保存在本机，不依赖 CDN。

重新安装或在另一个电脑上使用时，需要 Python 3.9–3.12；字体优先使用 macOS 的 Arial Unicode，Linux 可安装 DejaVu Sans。中文生成需要包含中文字形的字体，`comb/artwork.py` 的 `text_geometry` 可以改为指定本机字体。

```sh
git clone https://github.com/ChambersXDU/music-comb-studio.git
cd music-comb-studio
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m comb serve --port 8818
```

粘贴序列后自动更新 3D 模型。加入文字、SVG 或图片后，进入“图文排版”拖动图层，或输入 X、Y、宽度、旋转和深度。可以切换平齐嵌色、凹刻或凸起，以及前板、背板或两个面板。保存方案会下载可复现的 JSON，包含图形轮廓；打开方案会恢复参数。

## 音符格式

目前支持参考模型中已经校准的 20 个音符，按以下顺序递增：

```text
F Gb G Ab A Bb B C1 Db1 D1 Eb1 E1 F1 Gb1 G1 Ab1 A1 Bb1 B1 C2
```

空格、英文/中文逗号、换行都可分隔。`F#` 会归一化为 `Gb`，其余支持的升号同理；`·` 表示停顿，`.`、`-`、`R` 也接受为停顿标记。每个音符或停顿对应一个齿，重复音符保留，允许 8–33 个位置。每个休止段使用一个标记，不按长短展开。试听每格 0.28 秒，停顿不发声；实物的停顿长短由手动拨奏控制。导出模型中的停顿使用参考细齿结构，没有调音根部，需要跳过或停手，不能保证这些齿无声。

`C1` 等数字沿用参考模型的八度标记。网页试听暂按 F3 至 C5 播放，用来检查旋律；参考文件没有提供实测频率，所以这不是打印件的频率承诺。

给 agent 的示例指令：

> 把旋律转为音乐梳子音符序列，只使用 F、Gb、G、Ab、A、Bb、B、C1、Db1、D1、Eb1、E1、F1、Gb1、G1、Ab1、A1、Bb1、B1、C2；输出 8–33 个实际音符，以空格分隔，重复音符保留，停顿位置写 ·，每个停顿段只写一个标记。不要输出数字编号或节奏说明。

可以先粘贴这段示例：

```text
C1 C1 G1 G1 A1 A1 G1 · F1 F1 E1 E1 D1 D1 C1
```

网页的逐齿“自由长度增量”单位为 mm，正值加长自由振动段，负值缩短。JSON 中 `offsets` 保存的是固定根部的位置增量，符号相反：正值使根部向齿尖延伸，自由段变短。`offsets` 按输入序列顺序对应。整体 `extension` 增量直接改变所有自由齿的长度，也改变框架深度；默认 0 保留参考长度。实物音高受材料、打印方向和参数影响，需要打印后用逐齿微调校准。

## 读谱 Skill

`skills/music-comb-score/` 包含 Codex skill、音符格式参考和确定性转换脚本。它要求先独立读谱，记录转音删减、统一移调及停顿位置，再与已有模型比较。脚本将已经读出的科学音高事件转为网页方案，不自动识别谱图。休止默认保留，实际停顿长短由手动拨奏控制。

在项目根目录安装：

```sh
mkdir -p ~/.codex/skills
cp -R skills/music-comb-score ~/.codex/skills/
```

在新的 Codex 对话中调用：

> $music-comb-score 为指定歌曲片段找谱，简化快速转音，保留休止，输出音乐梳子序列和方案 JSON。

转换脚本的输入字段和命令见 [序列格式](skills/music-comb-score/references/sequence-format.md)。

运行仓库中的人工示例：

```sh
python3 skills/music-comb-score/scripts/make_sequence.py \
  --input examples/score-events.json --transpose -5 --out outputs/score-plan.json
.venv/bin/python -m comb generate --config outputs/score-plan.json --out outputs/score-comb
```

## CLI 和 agent 调用

CLI 不需要启动网页，也不需要安装 OpenSCAD。所有尺寸单位是毫米，输出路径是文件名前缀。

```sh
.venv/bin/python -m comb generate \
  --notes "C1 C1 G1 G1 A1 A1 G1 · F1 F1 E1 E1 D1 D1 C1" \
  --text "LILT" --out outputs/my-comb
```

默认生成 STL、3MF、SCAD、方案 JSON 和几何清单。`--format stl`、`--format scad` 或 `--format 3mf` 可以只输出一种模型格式。网页保存的方案可直接传入 CLI：

```sh
.venv/bin/python -m comb generate --config examples/melody.json --out outputs/my-plan
.venv/bin/python -m comb generate \
  --notes "F C2 F C2 F C2 F C2" --svg examples/logo.svg \
  --target both --width 5 --y 40 --mode emboss --depth 0.4 \
  --out outputs/my-logo
```

`--image /absolute/path/image.png` 加入位图；深色区域形成轮廓。更完整的图层与逐齿设置用 JSON 表示：

```json
{
  "notes": "F Gb G Ab A Bb B C1",
  "offsets": [0, 0, 0.1, 0, 0, 0, 0, -0.1],
  "extension": 0,
  "layers": [{
    "kind": "text", "text": "我的旋律", "target": "back",
    "x": 0, "y": 40, "width": 18, "rotation": 0,
    "depth": 0.4, "mode": "engrave"
  }]
}
```

SVG/图片的图层可设置 `kind: "svg"` 或 `"image"`，再给 `file` 路径。相对路径以 CLI 当前目录为准。位图另有 `threshold`（默认 128）和 `invert`（默认 false）。轮廓数据由 CLI 自动生成，保存后不必保留外部图片文件。网页导入的方案包含原图数据，可继续修改位图阈值；CLI 输出只保证当前轮廓的复现。

## 导出文件

| 格式 | 用途 |
| --- | --- |
| STL | 三件零件的平铺打印摆盘，单位 mm，载入切片软件后可以按不相连实体拆分 |
| 3MF | 同样的打印摆盘，三件零件为独立对象，包含颜色和材料名称；这是通用 3MF，未附带 Bambu 打印配置 |
| SCAD | 独立参数源码，嵌入框架网格和图形轮廓，可在 OpenSCAD 中继续改动 |
| JSON | 网页/CLI 方案，可编辑、保存、复现 |
| manifest.json | 音符、齿根、自由长度、面板尺寸和网格信息，供 agent 或脚本核对 |

JSON 中的 `colors` 对象包含 `front`、`back`、`clip` 三个十六进制色值，如 `"#538d82"`。网页预览、3MF 和 SCAD 会保留这些颜色；STL 不含颜色。3MF 使用标准颜色属性，实际耗材仍需在切片软件中选择和对应，未写入某台打印机的 AMS 配置。

SCAD 顶部可以改 `front_color`、`back_color`、`clip_color`、`notes`、`offsets`、`extension` 和 `part`，齿数与框架宽度会随音符数量变化。`baked_art` 是网页导出的图层设置，顺序为目标面板、X、Y、宽度、旋转、深度和方式（engrave / emboss / inlay），轮廓与 SVG 色块已嵌入源码。`art_colors` 可以改各图层色块，新增原生图文使用 `extra_color`。要直接在 SCAD 中加入新文字或替换 SVG，可填写 `extra_text` 或 `extra_svg`，再调整 `extra_target`、`extra_x`、`extra_y`、`extra_width` 等参数。`extra_svg` 是 SCAD 相邻文件或绝对路径；SVG 文件要自行保留。原有嵌入图层要删除时，将对应 `baked_art` 项的宽度设为 0。

SVG 会保留纯色填充区域和遮挡顺序，支持最多 16 种颜色。在图层的“保留 SVG 配色”选项下，可分别更改每个色块；关闭后使用单一图案颜色。文字和位图使用选定的图案颜色。

**平齐嵌色**将图案分为面板中的独立材料区域，外侧表面与原面板一致，深度只向面板内部延伸。3MF 把底色和各色图案保存在同一零件的组件中，切片时按颜色指定耗材；材料颜色数可以在界面看到。STL 会合并材料区域，因此平齐图案的颜色不会出现在 STL 中。凹刻是留出凹槽，凸起则增加外侧高度。多色打印可用 AMS/其他换料方式，耗材槽数量需要覆盖实际使用的颜色；合并相同颜色会减少用料种类。

```sh
.venv/bin/python -m comb generate \
  --svg examples/multicolor.svg --mode inlay --width 22 \
  --target both --out outputs/flush-multicolor
.venv/bin/python -m comb generate \
  --notes "C1 C1 G1 G1 A1 A1 G1 ·" --text "LILT" \
  --mode inlay --art-color "#c84f4f" --out outputs/red-text
```

图文使用外侧底面，排版中的 X 向右、Y 向下，与 3D 模型的“外侧”视图一致。建议在 Y≈40 的底边面板放置较矮的图文。图片不是贴图，会转换为真实凹凸几何体；SVG 需要填充路径，文字和线条请先转轮廓。图文自动裁切到实体面板，图片最多 5 MB，最多 12 层。深度超过局部面板厚度会切穿该处，选择 0.2–0.6 mm 便于开始试印。

## 代码与验证

`comb/model.py` 包含音符解析、参考尺寸、梳齿、框架和布尔建模；`comb/artwork.py` 转换图文；`comb/scad.py` 导出参数源码；`comb/server.py` 仅监听 127.0.0.1。浏览器前端位于 `web/`。`assets/reference_*.npz` 是无文字 STL 中三个归一化零件的测量基准，`tools/rebuild_frames.py` 可以重建去齿框架。

```sh
.venv/bin/python -m unittest discover -s tests -v
node tests/test_sequence.mjs
```

验证覆盖齿数上下限、最高/最低音和空白、整体长度和逐齿微调、SVG 孔洞、位图、中英文凹刻/凸起、STL 每条边恰有两个邻接面、3MF 独立对象，以及默认音阶与参考体积的差异。示例 SCAD 已用 OpenSCAD 2021.01 实际渲染验证。平齐多色验证还检查每个材料网格闭合、三件装配对象、颜色保留，以及嵌入前后的外表面和高度一致。读谱脚本还验证统一移调、等音、延音与重新发音、默认保留休止和齿数限制；前端验证停顿位置与播放时间安排。几何检查不代替打印和实测调音。

本项目重新实现了可编辑模型，没有拿到 MakerWorld 的完整原始 SCAD。参考模型的来源记录在 [provenance.json](evidence/provenance.json)。项目新编写的软件和 Skill 使用 MIT 许可证；参考及衍生几何资源不由该许可证重新授权，详见 [NOTICE.md](NOTICE.md)。Three.js 的 MIT 许可证保留在 `web/vendor/three/LICENSE`。
