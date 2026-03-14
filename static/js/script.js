// 全局变量
let currentUser = null;
let currentToken = null;
let currentChatTarget = null;
let isGroupChat = false;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
    
    // 绑定事件
    bindEvents();
});

// 初始化页面
function initPage() {
    // 显示登录页面
    showSection('login-section');
    
    // 检查本地存储中的用户信息
    const savedUser = localStorage.getItem('coo-user');
    if (savedUser) {
        try {
            const userData = JSON.parse(savedUser);
            currentUser = userData;
            currentToken = userData.token;
            showSection('chat-section');
            loadUsers();
            loadGroups();
        } catch (e) {
            console.error('Failed to parse saved user data:', e);
        }
    }
}

// 绑定事件
function bindEvents() {
    // 导航链接
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('data-target');
            showSection(target);
        });
    });

    // 登录表单
    document.getElementById('login-form').addEventListener('submit', function(e) {
        e.preventDefault();
        login();
    });

    // 注册表单
    document.getElementById('register-form').addEventListener('submit', function(e) {
        e.preventDefault();
        register();
    });

    // 验证表单
    document.getElementById('verify-form').addEventListener('submit', function(e) {
        e.preventDefault();
        verify();
    });

    // 重新发送验证码
    document.getElementById('resend-code').addEventListener('click', resendVerification);

    // 在线状态表单
    document.getElementById('online-form').addEventListener('submit', function(e) {
        e.preventDefault();
        setOnline();
    });

    // 创建群组
    document.getElementById('create-group').addEventListener('click', createGroup);

    // 发送消息
    document.getElementById('send-message').addEventListener('click', sendMessage);
    document.getElementById('message-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// 显示指定部分
function showSection(sectionId) {
    // 隐藏所有部分
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // 显示指定部分
    document.getElementById(sectionId).classList.add('active');
    
    // 如果显示聊天部分，加载用户和群组
    if (sectionId === 'chat-section' && currentToken) {
        loadUsers();
        loadGroups();
    }
    
    // 如果显示联机部分，加载在线用户
    if (sectionId === 'online-section' && currentToken) {
        loadOnlineUsers();
    }
}

// 登录
function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const messageDiv = document.getElementById('login-message');
    
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ Username: username, Password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (response.ok) {
            currentUser = {
                CID: data.CID,
                Username: data.Username,
                token: data.access_token
            };
            currentToken = data.access_token;
            localStorage.setItem('coo-user', JSON.stringify(currentUser));
            showMessage(messageDiv, '登录成功', 'success');
            showSection('chat-section');
            loadUsers();
            loadGroups();
        } else {
            showMessage(messageDiv, data.message || '登录失败', 'error');
        }
    })
    .catch(error => {
        showMessage(messageDiv, '登录失败，请检查网络连接', 'error');
    });
}

// 注册
function register() {
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const messageDiv = document.getElementById('register-message');
    
    fetch('/api/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ Username: username, Email: email, Password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (response.ok) {
            showMessage(messageDiv, '注册成功，请检查邮箱获取验证码', 'success');
            // 跳转到验证页面
            showSection('verify-section');
            // 填充用户ID
            document.getElementById('verify-cid').value = data.CID;
        } else {
            showMessage(messageDiv, data.message || '注册失败', 'error');
        }
    })
    .catch(error => {
        showMessage(messageDiv, '注册失败，请检查网络连接', 'error');
    });
}

// 验证
function verify() {
    const cid = document.getElementById('verify-cid').value;
    const code = document.getElementById('verify-code').value;
    const messageDiv = document.getElementById('verify-message');
    
    fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ CID: cid, verification_code: code })
    })
    .then(response => response.json())
    .then(data => {
        if (response.ok) {
            showMessage(messageDiv, '验证成功，请登录', 'success');
            // 跳转到登录页面
            showSection('login-section');
        } else {
            showMessage(messageDiv, data.message || '验证失败', 'error');
        }
    })
    .catch(error => {
        showMessage(messageDiv, '验证失败，请检查网络连接', 'error');
    });
}

// 重新发送验证码
function resendVerification() {
    const cid = document.getElementById('verify-cid').value;
    const messageDiv = document.getElementById('verify-message');
    
    if (!cid) {
        showMessage(messageDiv, '请输入用户ID', 'error');
        return;
    }
    
    fetch('/api/auth/resend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ CID: cid })
    })
    .then(response => response.json())
    .then(data => {
        if (response.ok) {
            showMessage(messageDiv, '验证码已重新发送，请检查邮箱', 'success');
        } else {
            showMessage(messageDiv, data.message || '发送失败', 'error');
        }
    })
    .catch(error => {
        showMessage(messageDiv, '发送失败，请检查网络连接', 'error');
    });
}

// 设置在线状态
function setOnline() {
    const frpId = document.getElementById('frp-id').value;
    const messageDiv = document.getElementById('online-message');
    
    if (!currentToken) {
        showMessage(messageDiv, '请先登录', 'error');
        return;
    }
    
    fetch('/api/online', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${currentToken}`
        },
        body: JSON.stringify({ CFD: frpId })
    })
    .then(response => response.json())
    .then(data => {
        if (response.ok) {
            showMessage(messageDiv, '在线状态设置成功', 'success');
            loadOnlineUsers();
        } else {
            showMessage(messageDiv, data.message || '设置失败', 'error');
        }
    })
    .catch(error => {
        showMessage(messageDiv, '设置失败，请检查网络连接', 'error');
    });
}

// 加载用户列表
function loadUsers() {
    if (!currentToken) return;
    
    fetch('/api/users', {
        headers: {
            'Authorization': `Bearer ${currentToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        const userList = document.getElementById('user-list');
        userList.innerHTML = '';
        
        data.forEach(user => {
            if (user.CID !== currentUser.CID) {
                const li = document.createElement('li');
                li.textContent = user.Username;
                li.addEventListener('click', function() {
                    selectChatTarget(user.CID, user.Username, false);
                });
                userList.appendChild(li);
            }
        });
    })
    .catch(error => {
        console.error('Failed to load users:', error);
    });
}

// 加载群组列表
function loadGroups() {
    if (!currentToken) return;
    
    fetch('/api/groups', {
        headers: {
            'Authorization': `Bearer ${currentToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        const groupList = document.getElementById('group-list');
        groupList.innerHTML = '';
        
        data.forEach(group => {
            const li = document.createElement('li');
            li.textContent = group.name;
            li.addEventListener('click', function() {
                selectChatTarget(group.id, group.name, true);
            });
            groupList.appendChild(li);
        });
    })
    .catch(error => {
        console.error('Failed to load groups:', error);
    });
}

// 加载在线用户
function loadOnlineUsers() {
    if (!currentToken) return;
    
    fetch('/api/online', {
        headers: {
            'Authorization': `Bearer ${currentToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        const onlineUsers = document.getElementById('online-users');
        onlineUsers.innerHTML = '';
        
        data.forEach(user => {
            const li = document.createElement('li');
            li.textContent = `用户ID: ${user.CID}, FRP ID: ${user.CFD}`;
            onlineUsers.appendChild(li);
        });
    })
    .catch(error => {
        console.error('Failed to load online users:', error);
    });
}

// 选择聊天目标
function selectChatTarget(targetId, targetName, isGroup) {
    currentChatTarget = targetId;
    isGroupChat = isGroup;
    document.getElementById('chat-title').textContent = targetName;
    loadMessages();
}

// 加载消息
function loadMessages() {
    if (!currentToken || !currentChatTarget) return;
    
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
    
    let url;
    if (isGroupChat) {
        url = `/api/groups/${currentChatTarget}/messages`;
    } else {
        url = `/api/messages/${currentChatTarget}`;
    }
    
    fetch(url, {
        headers: {
            'Authorization': `Bearer ${currentToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        data.forEach(message => {
            const messageDiv = document.createElement('div');
            messageDiv.className = message.sender_id === currentUser.CID ? 'message sent' : 'message received';
            messageDiv.textContent = message.content;
            chatMessages.appendChild(messageDiv);
        });
        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(error => {
        console.error('Failed to load messages:', error);
    });
}

// 发送消息
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value.trim();
    
    if (!currentToken || !currentChatTarget || !content) return;
    
    let url, body;
    if (isGroupChat) {
        url = `/api/groups/${currentChatTarget}/messages`;
        body = { content: content };
    } else {
        url = '/api/messages';
        body = { receiver_id: currentChatTarget, content: content };
    }
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${currentToken}`
        },
        body: JSON.stringify(body)
    })
    .then(response => response.json())
    .then(data => {
        if (response.ok) {
            messageInput.value = '';
            loadMessages();
        }
    })
    .catch(error => {
        console.error('Failed to send message:', error);
    });
}

// 创建群组
function createGroup() {
    const groupName = prompt('请输入群组名称:');
    if (!groupName) return;
    
    if (!currentToken) {
        alert('请先登录');
        return;
    }
    
    fetch('/api/groups', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${currentToken}`
        },
        body: JSON.stringify({ name: groupName })
    })
    .then(response => response.json())
    .then(data => {
        if (response.ok) {
            loadGroups();
        }
    })
    .catch(error => {
        console.error('Failed to create group:', error);
    });
}

// 显示消息
function showMessage(element, text, type) {
    element.textContent = text;
    element.className = `message ${type}`;
    
    // 3秒后清除消息
    setTimeout(() => {
        element.textContent = '';
        element.className = 'message';
    }, 3000);
}
