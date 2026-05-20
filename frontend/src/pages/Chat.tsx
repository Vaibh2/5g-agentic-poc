import React, { useState, useRef, useEffect } from "react";
import { apiService } from "../services/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export const Chat: React.FC = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const response = await apiService.chat(userMessage);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.response },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${(error as Error).message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    try {
      await apiService.clearChat();
      setMessages([]);
    } catch (error) {
      console.error("Error clearing chat:", error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const exampleCommands = [
    "deploy config v24",
    "inject anomaly",
    "rollback dep_123",
    "show metrics",
    "what caused the last incident?",
  ];

  return (
    <div className="space-y-6 h-[calc(100vh-140px)] flex flex-col">
      <div>
        <h1 className="text-2xl font-bold">Network Assistant</h1>
        <p className="text-gray-400 mt-1">
          Ask questions or trigger actions like deployments, rollbacks, etc.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 bg-dark-800 border border-dark-700 rounded-xl p-4 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="mb-4">Start a conversation...</p>
              <div className="space-y-2 text-sm">
                {exampleCommands.map((cmd) => (
                  <button
                    key={cmd}
                    onClick={() => setInput(cmd)}
                    className="block mx-auto text-blue-400 hover:text-blue-300"
                  >
                    "{cmd}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx}>
                <div
                  className={`font-medium ${
                    msg.role === "user" ? "text-blue-400" : "text-green-400"
                  }`}
                >
                  {msg.role === "user" ? "You:" : "Assistant:"}
                </div>
                <div className="text-gray-300 mt-1 whitespace-pre-wrap">
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="text-gray-500 italic">Thinking...</div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-4">
        <div className="flex-1">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="input-field w-full"
          />
        </div>
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="btn-primary disabled:opacity-50"
        >
          Send
        </button>
        <button onClick={handleClear} className="btn-secondary">
          Clear
        </button>
      </div>

      {/* Example Commands */}
      <div className="text-sm text-gray-500">
        <span className="font-medium">Example commands:</span>
        <div className="mt-2 flex flex-wrap gap-2">
          {exampleCommands.map((cmd) => (
            <button
              key={cmd}
              onClick={() => setInput(cmd)}
              className="text-blue-400 hover:text-blue-300"
            >
              {cmd}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};