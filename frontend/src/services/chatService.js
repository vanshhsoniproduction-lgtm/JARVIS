import {
  fetchConversationsBackend,
  saveConversationBackend,
  deleteConversationBackend,
} from "@/lib/api";

const STORAGE_KEY = "jarvis_conversations_v1";

export function getConversations() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return getDefaultConversations();
    return JSON.parse(raw);
  } catch (e) {
    return getDefaultConversations();
  }
}

export function saveConversations(conversations) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  } catch (e) {
    console.error("Failed to save conversations", e);
  }
}

export async function syncConversationsWithBackend() {
  try {
    const res = await fetchConversationsBackend();
    if (res.conversations && res.conversations.length > 0) {
      saveConversations(res.conversations);
      return res.conversations;
    }
  } catch (e) {
    console.error("Backend sync failed", e);
  }
  return getConversations();
}

export function createNewConversation(title = "New Conversation", workspaceId = "default") {
  const conversations = getConversations();
  const newConv = {
    id: `conv_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
    title,
    workspaceId,
    pinned: false,
    archived: false,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: [],
  };
  const updated = [newConv, ...conversations];
  saveConversations(updated);
  saveConversationBackend(newConv);
  return newConv;
}

export function getConversationById(id) {
  const conversations = getConversations();
  return conversations.find((c) => c.id === id) || null;
}

export function updateConversationMessages(id, messages, customTitle = null) {
  const conversations = getConversations();
  const index = conversations.findIndex((c) => c.id === id);

  let updatedConv;

  if (index === -1) {
    updatedConv = {
      id,
      title: customTitle || (messages[0]?.content ? messages[0].content.slice(0, 30) + "..." : "New Conversation"),
      workspaceId: "default",
      pinned: false,
      archived: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messages,
    };
    saveConversations([updatedConv, ...conversations]);
  } else {
    let title = conversations[index].title;
    if (title === "New Conversation" && messages.length > 0) {
      const firstUserMsg = messages.find((m) => m.role === "user");
      if (firstUserMsg) {
        title = firstUserMsg.content.slice(0, 35) + (firstUserMsg.content.length > 35 ? "..." : "");
      }
    }
    if (customTitle) title = customTitle;

    updatedConv = {
      ...conversations[index],
      title,
      messages,
      updatedAt: new Date().toISOString(),
    };
    conversations[index] = updatedConv;
    saveConversations(conversations);
  }

  saveConversationBackend(updatedConv);
  return updatedConv;
}

export function togglePinConversation(id) {
  const conversations = getConversations();
  const updated = conversations.map((c) => (c.id === id ? { ...c, pinned: !c.pinned } : c));
  saveConversations(updated);
  const target = updated.find((c) => c.id === id);
  if (target) saveConversationBackend(target);
  return updated;
}

export function renameConversation(id, newTitle) {
  const conversations = getConversations();
  const updated = conversations.map((c) => (c.id === id ? { ...c, title: newTitle } : c));
  saveConversations(updated);
  const target = updated.find((c) => c.id === id);
  if (target) saveConversationBackend(target);
  return updated;
}

export function deleteConversation(id) {
  const conversations = getConversations();
  const updated = conversations.filter((c) => c.id !== id);
  saveConversations(updated);
  deleteConversationBackend(id);
  return updated;
}

function getDefaultConversations() {
  const initial = [
    {
      id: "conv_default_fresh",
      title: "New Session",
      workspaceId: "default",
      pinned: false,
      archived: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messages: [],
    },
  ];
  saveConversations(initial);
  return initial;
}
