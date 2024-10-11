# shu-course-data

基于 GitHub Actions 的 SHU 课程爬虫，为 [SHU 排课助手](https://github.com/shuosc/shu-scheduling-helper) 和 [SHU 排课助手(v3)](https://github.com/shuosc/shu-scheduling-helper/tree/v3) 项目服务。

[![Interval Crawler Task](https://github.com/shuosc/shu-course-data/actions/workflows/interval-crawler-task.yml/badge.svg?branch=main)](https://github.com/shuosc/shu-course-data/actions/workflows/interval-crawler-task.yml)
[![Publish to COS](https://github.com/shuosc/shu-course-data/actions/workflows/publish-to-cos.yml/badge.svg?branch=data)](https://github.com/shuosc/shu-course-data/actions/workflows/publish-to-cos.yml)
[![Publish to COS](https://github.com/shuosc/shu-course-data/actions/workflows/publish-to-oss.yml/badge.svg?branch=data)](https://github.com/shuosc/shu-course-data/actions/workflows/publish-to-oss.yml)

## 说明

### 本项目的两个工作流

1. **Interval Crawler Task —
   [位于`main`分支](https://github.com/shuosc/shu-course-data/blob/main/.github/workflows/interval-crawler-task.yml)**

   抓取课程数据：
   - `crawler.py` - xk.autoisp.shu.edu.cn 的爬虫；
   - `src/index.ts` - jwxk.shu.edu.cn 的爬虫；
   
   分析课程数据变化并推送数据到 `data` 分支（或创建 Pull Request 人工复审）：`post_crawler.py`；

2. **Publish to COS —
   [位于`data`分支](https://github.com/shuosc/shu-course-data/blob/data/.github/workflows/publish-to-cos.yml)**

   上传到腾讯云 COS：`cos_publish.py`。

3. **Publish to OSS —
   [位于`data`分支](https://github.com/shuosc/shu-course-data/blob/data/.github/workflows/publish-to-oss.yml)**

   上传到阿里云 OSS：`oss_publish.py`，兼容当前版本的 [SHU 排课助手](https://github.com/shuosc/shu-scheduling-helper)。

### 课程数据格式

`data`分支下的目录结构如下：

```
/
├ terms
│ ├ 20212.json
│ ├ 20213.json
│ …
└ current.json
```

`terms`目录下的每个文件以`{termId}.json`格式命名，内容包括学期的元数据和详细的课程数据。具体数据结构如下：

| 字段            | 类型       | 说明                                                         |
| --------------- | ---------- | ------------------------------------------------------------ |
| `course`        | `Course[]` | 课程数据（`Course`具体字段略）                               |
| `termName`      | `string`   | 学期名称                                                     |
| `backendOrigin` | `string`   | 学校选课系统后端 Origin， `http://xk.autoisp.shu.edu.cn` 或 `https://jwxk.shu.edu.cn` |
| `hash`          | `string`   | Python 下通过`json.dumps`函数将`course`字段的值转为 JSON 格式（`sort_keys=True`，其他参数默认），对该 JSON 文本取 MD5 的值；JS 下对 `courses`字段以 key 进行排序后通过`JSON.stringfy`函数转为 JSON 格式，取文本的 MD5 值。用以标识本学期数据的版本 |
| `updateTimeMs`  | `number`   | 数据抓取时间，单位毫秒（ms）                                 |

`current.json`内容为`termId`数组，即当前选课系统中开放的学期。

### 数据发布到对象存储服务（COS）

数据发布到对象存储服务（当前为腾讯云 COS）前，需要对数据格式进行转换，**以更好地利用缓存机制，减少 CDN 回源流量和用户在网页端消耗的流量**。

发布到对象存储服务的有清单文件`manifest`和学期课程数据文件`terms/{termId}.{hash}.json`。180 天没有更新且不是当前选课系统开放的学期将不被列入清单文件，相关课程数据也不会被上传。对象存储服务会清理 360
天没有更新的学期课程数据文件。

#### `manifest`

**Header：**`Cache-Control=no-cache`

此文件较小，通过`Cache-Control`禁用了缓存，以确保用户及时获得课程数据更新信息。但在实践中 CDN 设置了过期时间为 1 分钟的强制缓存，以减少部分回源请求。

| 字段      | 类型         | 说明                                                         |
| --------- | ------------ | ------------------------------------------------------------ |
| `terms`   | `TermMeta[]` | 课程元数据，字段有：`termId`、`termName`、`hash`和`updateTimeMs` |
| `current` | `string[]`   | 当前选课系统开放的学期`termId`                               |

#### `terms/{termId}.{hash}.json`

**Header：**`Cache-Control=public, max-age=2592000`

文件内容为课程信息数组，即`Course[]`（字段略），上传后不允许变更，因此在 CDN 和浏览器端强缓存。文件原始大小通常为 1 ~ 2 MB，但通过 Gzip 或 Brotli 压缩后实际传输的数据量仅为原始大小的 10% 左右。

## 进度

### 已完成

- [x] 通过 OpenVPN 客户端连入学校网络
- [x] 实现在 Actions 环境下运行爬虫
- [x] 抓取选课网站课程列表写入文件
- [x] 将爬虫结果与当前数据进行比较，对于纯一般字段变化（如人数、容量、上课地点等），直接 PUSH 到新的分支，否则创建 Pull Request 以提供人工复查
- [x] 通过 Actions 自动将 data 分支数据上传到腾讯云 COS
- [x] 优化 Pull Request 创建的策略，可复用已有的拉取请求

### TODO List

- [ ] 继续优化 Pull Request 创建的策略，例如生成变更概览页面展示变化的字段、优化比较策略减少人工复审频率等
- [ ] 为爬虫部分添加其他平台工作流文件或本地运行 Docker 镜像等，防止当前 GitHub Actions 途径出现问题
- [ ] 抓取添加更多元信息，例如每天课程数、每节课的时间段、课程详细信息等
- [ ] ……

### 新选课系统后端的适配

*Work in Progress..*
支持爬取来自 `https://jwxk.shu.edu.cn/` 选课系统的课程数据（#584）

自 2024-2025 学年冬季学期选课开始，新的选课系统多次开启测试，且优于 xk.autoisp 提前放出冬季学期选课数据
猜测学校教务部有意加快使用新系统的推进节奏，因此特地跟进开发新的爬虫后端

现阶段要处理的任务：

 - [ ] 支持解析处理新选课系统的课程数据并转换到同样的数据格式
 - - [x] 支持抓取课程数据
 - - [x] GitHub Action 工作流验证
 - - [ ] 支持正确判断选课限制
 - - [ ] 数据正确性的验证
 - [ ] 解决在双系统并行时的数据决策问题（使用新数据还是旧数据）
 - [ ] 优化项目的文件结构

目前遇到的棘手的问题：

 - 新选课系统前后端分离，数据爬取方便，但是数据结构异常难懂（拼音首字母变量）
 - 新选课系统耦合了多所大学的选课逻辑（如候补选课、男女生课容量等等），需要确定各个字段对于我校的实际作用
 - 新选课系统的选课限制等具体细节实现方法不明，需要一次完整轮次的选课才可以确定

## 开发

### GitHub Actions 开发

- Fork 为自己的项目
- 到 Settings - Secrets 添加两条 Repository secrets：
    - `SHU_USERNAME` 学工号
    - `SHU_PASSWORD` 密码
- 进行开发

### 本地运行爬虫

前提：`pipenv` 已安装。 (`pip install pipenv`)

先 Clone 到本地。

```bash
pipenv install
pipenv run python crawler.py -u <学号>
```

如需查看所有爬虫命令，输入`pipenv run python crawler.py -h`。

## 许可证

**代码：** [AGPL-3.0-or-later](https://github.com/shuosc/shu-course-data/main/LICENSE)

基于此项目提供服务，包括发布程序运行结果以供下载，**必须**
以相同许可证开源提供服务的源码和修改后的源码（如有）。

**数据：** [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)

使用数据的服务请标注本项目地址，禁止商用，演绎版本需以相同方式共享。

---

*获取数据或使用数据提供服务时，请遵守各地法律法规。请勿滥用。*
