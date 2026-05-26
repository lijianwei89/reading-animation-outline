---
name: reading-animation-outline
description: Expand Chinese reading-subject animation outlines into production-ready animated scripts and generate visual-development prompts plus preview images. Use when the user provides a short animation outline, story beat list, lesson-intro animation idea, reading comprehension story setup, character dialogue summary, or examples like "导入动画", "动画大纲", "毛格利的危机", and asks to extend it into detailed scenes with locations, time of day, camera/action descriptions, narration, dialogue, emotions, transitions, main-character/scene/prop prompts, or gpt-image-2 preview artwork in a 3D Chinese comics style.
---

# Reading Animation Outline

## Goal

Transform a user-provided Chinese animation outline for a reading lesson into a polished segmented animation script. Preserve the original story intent, characters, key conflict, and learning-entry purpose while expanding sparse beats into vivid screen action, dialogue, narration, emotion labels, scene headings, and transitions. After the complete script, append image-generation prompts for the main visual assets and generate preview images with `gpt-image-2`.

## Non-Negotiable Sequence

Always complete these phases in order:

1. Generate the expanded animation script by following the existing screenplay rules below.
2. Keep that script content unchanged after it is generated. Do not shorten, rewrite, replace, or merge screenplay passages merely to serve image generation.
3. Append an `【美术预览 Prompt】` section after the final screenplay paragraph.
4. Generate preview images from the appended prompts with the specified Python script.
5. Append an `【预览图】` section listing or displaying successfully generated local image files. If generation fails, report that failure in this final section without modifying the script or prompt appendix.

## Workflow

1. Parse the outline into story beats:
   - Identify title, framing notes, time shifts, locations, characters, conflict, call-to-action, and required lines.
   - Keep parenthetical notes as structural intent, not literal on-screen text unless useful.
   - Preserve proper nouns and character relationships exactly unless the user asks to rename them.

2. Build a scene sequence:
   - Use one scene heading per location/time block.
   - Prefer headings in this form: `地点—日` or `地点—夜`.
   - Split memory, present-time, action, and emotional turns into separate scenes when it improves clarity.
   - Use `切画面。`, `画面慢慢变为波纹。`, or similar concise transitions between scenes.

3. Expand each beat into animation-ready detail:
   - Add visual actions that can be animated clearly.
   - Add camera language only when it helps: `画面拉开`, `切特写`, `镜头跟随`, `画面慢慢推近`.
   - Add child-friendly physical comedy, reaction shots, and expressive details, but keep them consistent with the outline.
   - Use emotion labels in dialogue cues, such as `毛格利（开心地）：`.
   - Use narration sparingly to connect beats and preserve the reading-lesson tone.

4. Preserve and strengthen the educational setup:
   - Make the protagonist's problem clear.
   - Make the stakes concrete and easy for children to understand.
   - End with an invitation, question, or task hook when the original outline asks the audience for help.

5. After the expanded script is complete, derive the main characters, principal settings, and important props visible in that script.

6. Write image prompts and append them after the expanded script:
   - Generate prompts only for main or recurring characters, plot-critical locations, and visually meaningful props. Do not invent props just to fill categories.
   - Keep the character identity and setting facts consistent with the finished script.
   - Begin every prompt with `3D中国漫画风格，儿童教育动画，电影级质感，` and describe a single clear subject or scene.
   - For characters, describe recognizable appearance, clothing/accessories, pose, expression, clean presentation background, and full-body or half-body framing suitable as a reference asset.
   - For scenes, describe location layout, time of day, lighting, atmosphere, key environmental features, and an empty or lightly populated composition suitable as a background reference.
   - For props, describe form, materials, colors, condition, and clean isolated presentation suitable as a prop reference.
   - Add `画面中不要出现任何文字、字幕、LOGO或水印。` to every prompt.

7. Generate preview images from each appended prompt unless the user explicitly asks for prompts only:
   - Use the image generation script bundled with this skill at `scripts/test_image_generation_api.py` (relative to this skill's directory).
   - Use model `gpt-image-2` and default size `1024x1024`, unless the user specifies another supported size.
   - Pass API credentials only through `TAL_MLOPS_API_KEY` or `TAL_MLOPS_APP_ID` plus `TAL_MLOPS_APP_KEY`; never embed or print credentials in the script output.
   - Save files to an output folder created for the task, using stable ASCII filenames such as `character-mowgli.png`, `scene-bee-valley.png`, or `prop-vine.png`.
   - Generate one image per listed prompt. If a category has no plot-relevant item, omit that category and do not issue an unnecessary API call.
   - If an image call fails or times out, keep the generated script and prompts intact, state which preview failed, and do not silently substitute a different story element.

## Output Format

Use this format:

```text
【动画一】标题

地点—日
图片: 图片URL或[待补充]
画面动作描述。
角色（情绪地）：
台词。

旁白（语气说明）：
旁白内容。

切画面。
地点—夜
...
```

Format rules:

- Write in Chinese.
- Put each dialogue speaker on its own cue line.
- Put longer dialogue on the following line after the colon.
- Use blank lines to separate action, narration, dialogue, and transitions.
- If the user provides an image URL, place it immediately after the most relevant first scene heading as `图片: URL`.
- If no image is provided and the output needs one, write `图片: [待补充]` only once near the first scene.
- Do not include markdown tables for scripts.
- Do not insert image prompt material into scene paragraphs. Append it only after the complete screenplay.
- Do not include implementation notes, rubrics, or explanations inside the screenplay unless requested.

After the screenplay, append this structure:

```text
【美术预览 Prompt】

主要人物｜角色名称
用途：角色参考图
Prompt：3D中国漫画风格，儿童教育动画，电影级质感，……画面中不要出现任何文字、字幕、LOGO或水印。

主要场景｜场景名称
用途：场景参考图
Prompt：3D中国漫画风格，儿童教育动画，电影级质感，……画面中不要出现任何文字、字幕、LOGO或水印。

重要道具｜道具名称
用途：道具参考图
Prompt：3D中国漫画风格，儿童教育动画，电影级质感，……画面中不要出现任何文字、字幕、LOGO或水印。

【预览图】
角色名称：/absolute/path/to/character-name.png
场景名称：/absolute/path/to/scene-name.png
道具名称：/absolute/path/to/prop-name.png
```

When responding in an interface that supports local image rendering, display a successful preview with Markdown image syntax using its absolute local path.

## Preview Generation Command

For each prompt, run:

```bash
python3 <SKILL_DIR>/scripts/test_image_generation_api.py \
  --model gpt-image-2 \
  --prompt '<美术预览 Prompt 中对应的完整提示词>' \
  --size 1024x1024 \
  --output '/absolute/output/folder/asset-name.png'
```

> `<SKILL_DIR>` 指本 skill 所在的目录。执行时替换为实际的绝对路径（即包含此 SKILL.md 文件的目录路径）。

The command must run with `TAL_MLOPS_API_KEY` or both `TAL_MLOPS_APP_ID` and `TAL_MLOPS_APP_KEY` available in its environment.

## Expansion Standards

Keep the script:

- Production-oriented: Every paragraph should describe something visible, audible, or directly useful for animation.
- Age-appropriate: Use clear emotions, simple motivations, vivid actions, and readable stakes.
- Faithful: Do not change the central plot, lesson hook, or ending request.
- Balanced: Expand thin outlines into multiple moments, but avoid padding with unrelated subplots.
- Performable: Dialogue should sound natural when voiced aloud.

For a short 3-5 sentence outline, usually create 3-5 scenes. For a dense outline with multiple parenthetical beats, create enough scenes to separate time shifts and location changes.

## Common Patterns

Memory-to-present structure:

```text
快乐回忆场景—日
展示快乐生活和关系。

切画面。
另一个快乐回忆场景—日/夜
强化"这是最快乐的时光"。

画面慢慢变为波纹。
现在的地点—日
转入危机和任务。
```

Crisis setup:

```text
角色A（严肃地）：
我收到情报，敌人要……

角色B（坚定地）：
我们必须……

角色B看向镜头，发出请求。
角色B（请求地）：
但我需要帮助，
你愿意……吗？
```

Child-friendly humor:

- Use harmless exaggeration: 被风吹起一点点、摔在柔软物体上、满头问号、眼睛一亮、冒出叹号。
- Keep danger readable but not frightening unless the user requests a tense style.
- Resolve comedy beats quickly so the story can return to the learning hook.

## Quality Checklist

Before finalizing, check that:

- The script includes clear scene headings with location and time.
- All required characters and key lines from the outline remain present.
- The timeline is understandable, especially flashback versus present.
- Dialogue has emotion labels.
- Actions are concrete enough for an animator.
- The final hook addresses the viewer when requested.
- The screenplay body remains complete and unchanged before the appended prompt section.
- Every main visual asset named in the prompt appendix comes directly from the script.
- Every preview prompt specifies `3D中国漫画风格` and prohibits visible text, logos, and watermarks.
- Each successful preview image was generated from its corresponding appended prompt using `gpt-image-2`.
