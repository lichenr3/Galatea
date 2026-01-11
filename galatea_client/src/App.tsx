import { ChatLayout } from './features/Chat/ChatLayout';
import { LanguageProvider } from './i18n/LanguageContext';
import './App.css'; 

function App() {
  return (
    <LanguageProvider>
      <div className="app-container">
        <ChatLayout />
      </div>
    </LanguageProvider>
  );
}

export default App;