<template>
  <h1>代办记事</h1>
  <input v-model="todoText" placeholder="输入代办" @keyup.enter="addTodo"/>
  <button @click="addTodo">添加</button>

  <!-- v-if 分支：无数据提示 -->
  <p v-if="todoList.length === 0">暂无代办</p>

  <!-- v-for 循环渲染代办 -->
  <ul v-else>
    <li v-for="item in todoList" :key="item.id">
      <span v-if="item.done" style="text-decoration:line-through;color:#888;">
        {{ item.content }}
      </span>
      <span v-else>{{ item.content }}</span>
      <button @click="item.done = !item.done">完成</button>
      <button @click="delTodo(item.id)">删除</button>
    </li>
  </ul>
</template>

<script setup>
import { ref } from 'vue'
const todoText = ref('')
const todoList = ref([])

const addTodo = () => {
  const val = todoText.value.trim()
  if (!val) return
  todoList.value.push({
    id: Date.now(),
    content: val,
    done: false
  })
  todoText.value = ''
}

const delTodo = (id) => {
  todoList.value = todoList.value.filter(i => i.id !== id)
}
</script>

<style scoped>
ul{padding:0;list-style:none;}
li{margin:6px 0;gap:8px;display:flex;align-items:center;}
</style>