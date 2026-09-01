# Academic Slides Skill — 设计说明（精简版）

## 1. 定位

一个「研究者掌控科研故事、AI 负责思考辅助 + 工程实现 + 视觉迭代」的学术汇报工作流。

不是「把一堆图片自动变成 PPT」，而是把学术汇报从**手工排版任务**变成**人机协同**：
人决定「讲什么、为什么」，AI 帮忙「把它想清楚，并表达得足够好」。

第一版只支持 **LaTeX Beamer → PDF**，把「学术表达 + 稳定生成 + 自动视觉审计」做扎实。

### 一条硬规则（只说一次）

> AI 永远不从 `assets/` 里的图片反推完整科研故事。
> 故事缺失时进入 **Story Interview**：只提问、指出缺口、给候选结构，**不擅自替研究者定稿**。
> 反例：看到 3 张图就自动生成 30 页 slides，编造缺失的科学连接。

## 2. 三个阶段（不是四个 Mode）

| 阶段 | 触发 | AI 做什么 | 门槛 |
|---|---|---|---|
| **Story** | outline 缺失或不完整 | interview（提问，每轮 ≤3 个阻塞问题）或 review（查 claim–evidence、逻辑断裂、时间分配） | 研究者确认 narrative 后才继续 |
| **Production** | story 已确认 | asset 归一化 → slide-map → 写 Beamer → 编译 | slide-map 变更需研究者确认 |
| **Visual Audit** | 编译出 PDF | 渲染每页 → 拼 contact sheet → 先整体看、再放大可疑页 → 修 → 重编 | 直到通过检查 |

原设计的 Mode A（interview）与 Mode B（review）本质都是「story 定稿前」，合并为一个 Story 阶段。

## 3. 视觉反馈循环（核心卖点，也是最难的一环）

```
confirmed story → slide-map → LaTeX → compile → render pages
   → contact sheet（先整体） → 放大可疑页（按需，省 token） → 修 → 重编
```

工程前提（SKILL.md 会做环境检测并降级）：

- **编译**：`latexmk -xelatex`（中文/好字体需要 xelatex），无则回退 `xelatex` 两遍。
- **渲染**：优先 PyMuPDF（`pip install pymupdf`，纯 Python，本仓已验证可用）；无则回退 `pdftoppm`。
- **溢出检测**：`check_overflow.py` 用词级 bbox 找「文字撞页脚 / 跑出画布」，PyMuPDF 或 `pdftotext` 双后端。
- **成本策略**：30 页不逐页读图。先看一张 contact sheet 做整体判断，只对脚本标记的可疑页放大逐页多模态读。

## 4. Asset 归一化（原设计缺失，必须补）

`assets/` 里可能有 `.svg`（Beamer 不能直接用）、`.mp4`（PDF 里不可靠播放）。
`normalize_assets.py` 统一处理：

- `svg → pdf`（PyMuPDF / rsvg / inkscape）
- `视频 → 关键帧 png`（提示研究者选帧；PDF 里只放静帧 + 角标）
- 质量检查：分辨率、DPI 估计、是否过小 → 输出 `assets/_normalized/` + 一张 mapping 报告

**Asset 的存在不代表必须进 slides**；slides 服务于故事。

## 5. 每页一个问题

每页回答：`Slide Question → Main Message → Evidence/Visual`。
标题服务于结论：不是 "Cross Correlation"，而是 "ERK activation precedes cell extension"。

## 6. 视觉原则（第一版从简）

- 一页一个主要结论，超载就拆页。
- 图优先：`figure + one sentence`，不是 `6 bullets + tiny figure`。
- 图要足够大：听众看不清 axis/legend/error bar，这张图就没完成任务。
- 论文 figure 可 crop/放大/加箭头/加注释，但**不得修改 scientific data**。
- 反 AI 味：禁止滥用 `itemize`；相邻页用不同版式；80% 页面用段落式写作。
  （详见 `references/writing-style.md` 的 6 个组合模式）

## 7. 目录约定

**用户每次汇报的项目**（`new_talk.py` 脚手架生成）：

```
my-talk/
├── brief.md            # 听众、时长、目标、风格、约束
├── outline.md          # 研究者确认过的 scientific narrative
├── slide-map.md        # 每页 question/message/visual（AI 生成，研究者可改）
├── assets/             # 研究者放素材
│   └── _normalized/    # 脚本产物：svg→pdf、视频→帧
├── references.bib
├── slides.tex          # AI 生成
└── build/
    ├── slides.pdf
    ├── pages/          # 每页 png
    └── contact-sheet.png
```

**Skill 自带**（本仓库）：

```
academic-slides/ (= 本 skill 根)
├── SKILL.md            # 运行时主指令（薄，指向 references/）
├── references/         # 按需加载：story / writing-style / layouts / visual-audit
├── templates/          # academic.tex + 主题 .sty + brief/outline/slide-map 模板
└── scripts/            # normalize_assets / build / render_pages / contact_sheet / check_overflow / new_talk
```

## 8. 人机分工

| 环节 | Researcher | AI |
|---|---|---|
| 科研问题 / claim / story | 决定 | 提问、质疑、给候选结构 |
| Evidence | 提供、判断 | 整理、匹配 claim |
| slide 顺序 / layout | 审核、可干预 | 设计 |
| LaTeX / 编译 / 视觉 QA | 不必手写 | 负责，自动检查 |

## 9. 第一版明确不做（防 scope creep）

自动解析整篇论文、自动生成完整科研故事、多 backend（Marp/Slidev/PPTX）、自动联网查文献、
自动生成复杂插图、未经确认重写 scientific claim。都留待以后。

## 10. 成功标准

1. 给清晰大纲 → 稳定产出**可直接继续改**的学术汇报。
2. 给不完整大纲 → 先帮研究者把故事想清楚，而不是直接吐 PPT。
3. 研究者说「这页强调 X 不要 Y」→ 准确落实。
4. 通过 render → 审计主动发现：图太小 / 字太多 / 页面挤 / 结论不突出。
5. 研究者的时间从「调 LaTeX 坐标、处理溢出」变回「科学内容与表达判断」。

---

*参考：[Faust-Donf/beamer-academic](https://github.com/Faust-Donf/beamer-academic)
（学术 Beamer 主题与反-AI 写作范式）、
[dro42/presentation-kit](https://github.com/dro42/presentation-kit)
（skill 工程组织与 `slide-overflow-check` 视觉审计）。*
