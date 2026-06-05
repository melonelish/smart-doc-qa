<template>
  <div class="message assistant">
    <div class="message-avatar">🤖</div>
    <div class="message-bubble">
      <div class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  gap: 10px;
  max-width: 85%;
  align-self: flex-start;
  animation: fadeInUp 0.3s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
  color: #fff;
}
.message-bubble {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 12px;
  background: var(--bg-input);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}
.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typing 1.4s infinite;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}
</style>
