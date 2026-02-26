import fs from 'fs'
import path from 'path'
import axios from 'axios'
import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'

import { removePunctuation, randomizeSentence, splitTextByPeriod } from './utils/text.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const filePath = path.resolve(__dirname, 'data/刀削面')

// --- 解析命令行参数 ---
// 使用方式: node script.js --sessionid 12345
const args = process.argv.slice(2) // 去掉 node 和 文件路径
let sessionId = 846307 // 默认值

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--sessionid' && args[i + 1]) {
    sessionId = Number(args[i + 1])
    break
  }
}

console.log(`[启动] 使用的 Session ID: ${sessionId}`)

// 主函数：执行一次完整的流程
async function executeCycle() {
  try {
    // 1. 读取主模板文件
    let content = fs.readFileSync(path.resolve(filePath, 'index.txt'), 'utf8')

    // 2. 读取 models 目录下的所有 .txt 文件，并替换占位符
    const modelFiles = fs.readdirSync(filePath)
    for (const item of modelFiles) {
      if (item === 'index.txt' || !item.endsWith('.txt')) continue
      const modelPath = path.resolve(filePath, item)
      if (!fs.statSync(modelPath).isFile()) continue

      const modelName = item.replace('.txt', '')
      const modelContent = fs.readFileSync(modelPath, 'utf8')
      const placeholder = new RegExp(`\\{${modelName}\\}`, 'g')
      content = content.replace(placeholder, randomizeSentence(modelContent))
    }

    // 3. 处理文本：打乱并按句号分割
    const sentences = splitTextByPeriod(randomizeSentence(content))

    // 4. 遍历每句话发送
    for (const item of sentences) {
      let processedItem = item

      // 替换时间占位符
      if (item.includes('CURRENT_TIME')) {
        const now = new Date();
        let hour = now.getHours();
        let minute = now.getMinutes();
        const second = now.getSeconds();

        // 如果秒数大于 50，则分钟进位
        if (second > 50) {
          minute += 1;
          
          // 处理分钟进位到小时的情况
          if (minute >= 60) {
            minute = 0;
            hour += 1;
            
            // 处理小时进位（24点制）
            if (hour >= 24) {
              hour = 0;
            }
          }
        }
        
        // 格式化时间文本：如果是整点（分钟为0），则显示“xx点整”
        const timeText = minute === 0 ? `${hour}点整` : `${hour}点${minute}分`;
        processedItem = processedItem.replaceAll('CURRENT_TIME', timeText)
      }

      // 发送文本到本地服务 (使用传入的 sessionId)
      await axios.post('http://localhost:8010/human', {
        text: processedItem,
        type: 'echo',
        interrupt: false,
        sessionid: sessionId
      })

      // 短暂延迟
      await new Promise(resolve => setTimeout(resolve, 100))

      // 获取服务端剩余播放时间
      const res = await axios.post('http://localhost:8010/get_remaining_duration', {
        sessionid: sessionId
      })

      // 等待播放完成
      if (res.data?.data > 0) {
        await new Promise(resolve => setTimeout(resolve, parseInt(res.data.data * 1000)))
      }
    }
  } catch (err) {
    console.error('执行循环时出错:', err)
  }
}

// 无限循环执行
async function startLoop() {
  while (true) {
    await executeCycle()
    console.log('[INFO] 一轮执行完成，即将开始下一轮...')
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
}

// 启动
startLoop()