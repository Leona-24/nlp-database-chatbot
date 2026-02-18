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
        schema,
        setSchema,
        dbConfig,
        setDbConfig,
        messagesEndRef,
        sendMessage
    } = useChat(onLogout);

    const suggestions = [
        "Show all students",
        "How many customers are there?",
        "List orders with total amount greater than 100",
        "Show me students with GPA > 3.5",
        "Show all customers from Chennai",
        "how many users are there",
    ];

    return (
        <div className="min-h-screen bg-slate-50 flex">
            <Sidebar
                connected={connected}
                dbConfig={dbConfig}
                setDbConfig={setDbConfig}
                setConnected={setConnected}
                schema={schema}
                setSchema={setSchema}
            />

            <div className="flex-1 flex flex-col">
                <Header
                    connected={connected}
                    username={user.username}
                    dbUsername={dbConfig.username}
                    onLogout={onLogout}
                />

                <MessageList
                    messages={messages}
                    connected={connected}
                    suggestions={suggestions}
                    onSuggestionClick={setInput}
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
