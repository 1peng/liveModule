// 处理文案
export function randomizeSentence(template) {
  // 递归函数，用于处理嵌套的 {} 和 |
  function processTemplate(str) {
    let result = ''
    let stack = []
    let currentPart = ''

    for (let i = 0; i < str.length; i++) {
      if (str[i] === '{') {
        if (stack.length === 0) {
          result += currentPart
          currentPart = ''
        }
        stack.push('{')
      } else if (str[i] === '}') {
        if (stack.length === 1) {
          const options = currentPart.split('|').map(option => option.trim())
          result += options[Math.floor(Math.random() * options.length)]
          currentPart = ''
        }
        stack.pop()
      } else {
        currentPart += str[i]
      }
    }

    result += currentPart
    return result
  }

  return processTemplate(template)
}

// 随机数组里的某个元素
export function getRandomObject(arr) {
  const index = Math.floor(Math.random() * arr.length)
  return arr[index]
}

// 分割语料
export function splitByPeriod(text) {
  const matches = text.split('。');
  const result = matches ? matches.map(match => match.trim()) : []
  return result
}

// export function splitTextByPeriod(text) {
//   // 按照句子分割
//   let sentences = text.split(/(?<=[。！？])\s*/);

//   // 处理不足20字的句子
//   for (let i = 0; i < sentences.length; ) {
//     if (sentences[i].length < 30) {
//       if (i === sentences.length - 1 && sentences[i].length < 30) {
//         sentences[i - 1] += sentences[i];
//         sentences.splice(i, 1); // 删除最后一个元素
//       } else {
//         // 合并当前句子与下一个句子
//         sentences[i] += sentences[i + 1];
//         sentences.splice(i + 1, 1); // 删除已经合并的下一个句子
//       }
//     } else {
//       i++; // 只有当当前句子满足条件（大于等于20字）时，才移动到下一个句子
//     }
//   }
//   return sentences;
// }

export function splitTextByPeriod(text, minLen = 40, maxLen = 60) {
  if (!text.trim()) return [];

  // 第一步：按句号、感叹号、问号分割，保留分隔符（使用正向先行断言）
  const rawSentences = text.split(/(?<=[。！？，])/).filter(s => s.trim());

  if (rawSentences.length === 0) return [text];

  const result = [];
  let current = '';

  for (const sentence of rawSentences) {
    const candidate = current + sentence;

    // 如果加上当前句后仍小于最小长度，先累积
    if (candidate.length < minLen) {
      current = candidate;
      continue;
    }

    // 如果当前累积 + 当前句 超过最大长度，但 current 非空，则先输出 current
    if (current && candidate.length > maxLen) {
      // 尽量不让 current 太短
      if (current.length >= minLen) {
        result.push(current);
        current = sentence;
      } else {
        // current 太短，只能硬切（或合并到下一段）
        result.push(candidate);
        current = '';
      }
    } else {
      // 候选长度在合理范围内，直接提交
      result.push(candidate);
      current = '';
    }
  }

  // 处理剩余部分
  if (current) {
    if (result.length > 0) {
      // 合并到最后一个段落（避免结尾太短）
      result[result.length - 1] += current;
    } else {
      result.push(current);
    }
  }

  // 最终清理：移除首尾空白
  return result.map(s => s.trim()).filter(s => s);
}

export function removePunctuation(text) {
  return text.replace(/\p{P}/gu, "");
}

export const SYSTEM_VARS = {
  'ONLINE_NICKNAME': '在线用户昵称',
  'CURRENT_TIME': '当前时间',
  'CURRNET_ONLINE_CNT': '当前在线人数',
  'NEXT_HOUR': '下个整点',
  'NEXT_HOUR_GAP': '下个整点间隔',
  'NEXT_TEN_MINUTE': '下个10分钟',
  'NEXT_TEN_MINUTE_GAP': '下个10分钟间隔',
  'REPLY_INTERACTION': '回答互动模版',
  'REPLY_CHAT': '回答公屏文字模版',
  'MUTE': '静音模版',
  'PRODUCT_LINK_NUM': '链接号',
  'PRODUCT_PRICE': '小黄车价格',
  'PRODUCT_BRAND': '商品品牌',
  'PRODUCT_NAME': '商品名称',
}

export function splitModels(str = '') {
  // 使用正则表达式匹配所有 {} 内的内容
  const matches = str.match(/\{[^{}]*\}/g);

  // 定义一个函数来递归处理嵌套的 {}
  function extractContent(match) {
    // 去除外层的大括号
    let content = match.slice(1, -1);
    // 如果内容中还有嵌套的 {}，则递归处理
    while (content.includes('{')) {
      const innerMatches = content.match(/\{[^{}]*\}/g);
      if (!innerMatches) break;
      innerMatches.forEach(innerMatch => {
        content = content.replace(innerMatch, extractContent(innerMatch));
      });
    }
    // 按照 | 分割内容
    return content.split('|').map(item => item.trim());
  }
  // 处理所有匹配项
  const array = matches.flatMap(match => extractContent(match)).filter((item) => {
    return str.includes(`{${item}}`) && !Object.keys(SYSTEM_VARS).includes(item)
  })
  const uniqueArray = [...new Set(array)]
  return uniqueArray
}
