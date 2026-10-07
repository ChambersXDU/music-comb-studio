# 序列、音域和转换

生成器使用实际音符标签，每个标签对应一个梳齿，顺序如下：

```text
F Gb G Ab A Bb B C1 Db1 D1 Eb1 E1 F1 Gb1 G1 Ab1 A1 Bb1 B1 C2
```

软件的试听映射为 F3–C5：`F` 对应 F3，`C1` 对应 C4，`C2` 对应 C5。这是转换脚本使用的逻辑音域，不能据此承诺打印件的实际频率。`C1` 是此项目标签，不等于科学音高记法里的 C1。

序列允许 8–33 个位置。空格、逗号、换行可分隔；生成器接受对应升号并归一化为降号。`·` 表示停顿，默认每个休止段保留一个标记，不编码长短。网页试听每格 0.28 秒，停顿格不发声；导出模型对应参考细齿结构，不保证物理无声，手动拨奏时在该位置跳过或停手。停顿也计入齿数。

方案 JSON 的最小格式是：

```json
{"notes":"F Gb G Ab A Bb B C1","offsets":[],"extension":0,"layers":[]}
```

`offsets` 是齿根位置增量，正值缩短自由振动段；网页“自由长度增量”显示相反符号。`extension` 改变整体齿长与面板深度。将序列填进现有网页时优先只替换序列，保留用户已经设置的图文、颜色与逐齿参数；若齿位对应关系改变，需要明确处理旧的逐齿调节。

## 确定性转换脚本

`scripts/make_sequence.py` 只转换已经读出并简化的音符，不读取图片，也不决定删哪些转音。输入使用科学音高记法，并保留歌词对位：

```json
{
  "source":{"url":"曲谱页面网址","page":1},
  "original_key":"F",
  "target_key":"C",
  "simplifications":["在此记录明确的删减或合并"],
  "events":[
    {"pitch":"F4","lyric":"字"},
    {"pitch":"A4","lyric":"字"},
    {"pitch":"A4","tie_to_previous":true},
    {"pitch":null},
    {"pitch":"F4","lyric":"字"}
  ]
}
```

上面只是字段示意，实际输入须转换出 8–33 个位置。同音再发音是两个事件；只有真正的同音延音线才能设 `tie_to_previous`。圆滑线不等于延音线。`pitch: null` 表示一个休止段，默认转换为一个 `·`。连续休止符属于同一停顿段时，读谱者先将其合成一个事件。原始时值可留在输入记录中；序列只标停顿位置，实际长短由手动拨奏控制。

```sh
python3 /path/to/music-comb-score/scripts/make_sequence.py \
  --input excerpt.events.json --transpose -5 --out excerpt.plan.json
```

`--transpose -5` 将 F4 移到 C4，输出标签 `C1`。`--octave-shift` 为整段统一升降八度，默认 0。脚本拒绝超出音域、无效延音或超过齿数范围的输入，不自动删音、逐音折叠八度或填充空白。它输出可载入网页的方案和同名前缀 `.score.json` 对位记录；休止默认转换为空白格；只有用户明确要求去掉停顿时使用 `--omit-rests`。

## 交给项目

在找到的 music-comb-studio 项目根目录运行：

```sh
.venv/bin/python -m comb generate --config /path/to/excerpt.plan.json --out outputs/excerpt
```

默认生成 SCAD、STL、3MF、方案和几何清单。独立 SCAD 可继续修改；多色嵌色使用 3MF。只有本机网页已运行、且用户要求填入时才通过浏览器输入序列并确认“模型已更新”。没有此项目也能交付序列和 JSON，不假称已生成几何模型。
