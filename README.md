# shu-course-data

基于 Github Actions 的 SHU 课程爬虫，为 [SHU 排课助手](https://github.com/shuosc/shu-scheduling-helper) 等项目服务。

## 进度

### 已完成

- [x] 通过 OpenVPN 客户端连入学校网络
- [x] 实现在 Actions 环境下运行爬虫
- [x] 抓取选课网站课程列表写入文件
- [x] 将文件 PUSH 到新的分支并创建 Pull Request 以提供人工复查
- [x] 通过 Actions 自动将 data 分支数据上传到腾讯云 COS
- [x] 优化 Pull Request 创建的策略，可复用已有的拉取请求

### TODOs

- [ ] 添加新的 Actions 对合并到 data 分支的数据进行校验，标识数据项变更及重要字段的变化，对于纯一般字段变化（如人数、容量、上课地点等），直接合并
- [ ] 抓取添加更多元信息，例如每天课程数、每节课的时间段等
- [ ] ……

## 开发

(以下流程未经试验，请 Contributors 麻烦核对，谢谢！)

### Github Actions 开发

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
pipenv shell
python crawler.py -u <学号>
```

如需查看所有爬虫命令，输入 `python crawler.py -h`。
