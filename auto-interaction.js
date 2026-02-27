const { post, get } = require('./utils/request');

// 发言内容库
const msgContents = [
  '当季新货山楂干，无熏无硫，没有任何添加。',
  '煮水，煲汤，炖肉，煮花茶，做山楂饼，山楂糕，山楂汁等吃法多种多样。',
  '七天无理由，运费险给您保驾护航，放心拍，放心带。',
  '今天福利价格10块9半斤，16块9一斤，先到先得。',
  '去籽无核，品质保证。'
];

// 回复模板
const replyTemplates = [
  '您好，感谢您的留言，我们会尽快为您解答',
  '感谢您的关注，关于这个问题，我们的产品确实是这样的',
  '您好，您的问题很有价值，我们会认真考虑',
  '感谢您的支持，我们会继续努力提供更好的产品和服务',
  '您好，关于这个问题，我可以为您详细解答'
];
// 欢迎来到直播间相关的回复
const welcomeReplies = [
  `欢迎 {nickname} 来到直播间！`,
  `热烈欢迎 {nickname} 加入我们！`,
  `欢迎 {nickname}，很高兴您能来！`,
  `{nickname} 来了，欢迎欢迎！`,
  `欢迎 {nickname} 来到我们的直播间，希望您喜欢这里！`
];

// 顺序获取发言内容
let msgIndex = 0;
function getSendMsg() {
  const content = msgContents[msgIndex];
  msgIndex = (msgIndex + 1) % msgContents.length;
  console.log(`[发言] ${content}`);
  return content;
}

// 随机获取回复模板
function getRandomReply() {
  const index = Math.floor(Math.random() * replyTemplates.length);
  return replyTemplates[index];
}

// 调用发言接口
async function sendMsg() {
  try {
    const content = getSendMsg();
    
    const response = await post('http://localhost:8000/post_live_msg', {
      content: content
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('[发言接口] 调用成功:', response);
  } catch (error) {
    console.error('[发言接口] 调用失败:', error);
  }
}

// 获取用户留言列表并回复
async function checkAndReplyComments() {
  try {
    // 获取用户留言列表
    const response = await get('http://localhost:8000/getmsg');
    
    // console.log('[留言列表] 调用成功，获取到评论:', response);
    
    // 处理返回的数据结构
    const comments = response?.data || [];
    
    for (const comment of comments) {
      // 检查badgeType是否为5
      const hasBadgeType5 = comment.badge_infos && comment.badge_infos.some(badge => badge.badgeType === 5);
      
      if (!hasBadgeType5) {
        console.log(`[回复] 用户: ${comment.nickname}, 内容: ${comment.content}`);
        
        // 准备回复内容
        let replyContent;
        if (comment.msgType === 10005 && comment.content === '来了') {
          replyContent = welcomeReplies[Math.floor(Math.random() * welcomeReplies.length)].replace('{nickname}', comment.nickname);
        } else {
          // 普通回复
          replyContent = getRandomReply();
        }
        
        // 回复评论的接口
        const replyResponse = await post('http://localhost:8000/post_live_app_msg', {
          content: replyContent,
          contact: comment.contact
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log('[回复接口] 调用成功:', replyResponse);
      } else {
        // console.log(`[跳过] 用户: ${comment.nickname}, 内容: ${comment.content} (badgeType为5)`);
      }
    }
  } catch (error) {
    console.error('[留言列表/回复] 调用失败:', error);
  }
}

// 20秒执行一轮发表留言，每3秒发表一次
async function startMsgCycle() {
  while (true) {
    console.log('[系统] 开始新一轮发言');
    
    // 按顺序发表所有留言
    for (let i = 0; i < msgContents.length; i++) {
      await sendMsg();
      
      // 除了最后一条，每条留言后等待3秒
      if (i < msgContents.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }
    
    console.log('[系统] 本轮发言结束，等待20秒后开始下一轮');
    await new Promise(resolve => setTimeout(resolve, 20000));
  }
}

// 定时检查并回复评论
setInterval(checkAndReplyComments, 3000);

// 初始执行
startMsgCycle();
checkAndReplyComments();

console.log('[系统] 自动交互脚本已启动，每3秒执行一次发言和评论回复');
