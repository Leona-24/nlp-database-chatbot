import { useEffect } from 'react';
import Sidebar from '../components/home/Sidebar';
import Header from '../components/home/Header';
import MessageList from '../components/home/MessageList';
import ChatInput from '../components/home/ChatInput';
import { useChat } from '../hooks/useChat';

interface HomeProps {
    user: { token: string; username: string };
    onLogout: () => void;
}

const Home = ({ user, onLogout }: HomeProps) => {
    const {
        messages,
        input,
        setInput,
        loading,
        connected,
        setConnected,
        setSchema,
        dbConfig,
        setDbConfig,
        messagesEndRef,
        sendMessage,
        clearMessages
    } = useChat(onLogout);

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'r') {
                event.preventDefault();
                clearMessages();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [clearMessages]);

    return (
        <div className="h-screen overflow-hidden bg-slate-50 flex">
            <Sidebar
                connected={connected}
                dbConfig={dbConfig}
                setDbConfig={setDbConfig}
                setConnected={setConnected}
                setSchema={setSchema}
            />

            <div className="flex-1 flex flex-col min-h-0">
                <Header
                    username={user.username}
                    onLogout={onLogout}
                />

                <MessageList
                    messages={messages}
                    connected={connected}
                    messagesEndRef={messagesEndRef}
                />

                <ChatInput
                    input={input}
                    setInput={setInput}
                    sendMessage={sendMessage}
                    connected={connected}
                    loading={loading}
                />
            </div>
        </div>
    );
};

export default Home;
