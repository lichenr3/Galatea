import React, { useState, useEffect, useRef } from 'react';
import type { CharacterContact } from '../../../types';
import { useLanguage } from '../../../i18n/LanguageContext';
import './ContactList.css';

interface Props {
    contacts: CharacterContact[];
    activeSessionId: string | null;
    onSelectContact: (sessionId: string) => void;
    onAddContact: () => void;
    onDeleteSession: (sessionId: string) => void;
}

export const ContactList: React.FC<Props> = ({ 
    contacts, 
    activeSessionId, 
    onSelectContact,
    onAddContact,
    onDeleteSession
}) => {
    const { t } = useLanguage();
    const [expandedChars, setExpandedChars] = useState<Set<string>>(new Set());
    const [openMenuSessionId, setOpenMenuSessionId] = useState<string | null>(null);
    const [menuPosition, setMenuPosition] = useState<{top: number, left: number} | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-expand active character
    useEffect(() => {
        if (activeSessionId) {
            const char = contacts.find(c => c.sessions.some(s => s.sessionId === activeSessionId));
            if (char) {
                setExpandedChars(prev => {
                    const next = new Set(prev);
                    next.add(char.characterId);
                    return next;
                });
            }
        }
    }, [activeSessionId, contacts]);

    const toggleChar = (charId: string) => {
        setExpandedChars(prev => {
            const next = new Set(prev);
            if (next.has(charId)) next.delete(charId);
            else next.add(charId);
            return next;
        });
    };

    const toggleMenu = (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        if (openMenuSessionId === sessionId) {
            setOpenMenuSessionId(null);
            setMenuPosition(null);
        } else {
            const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
            setOpenMenuSessionId(sessionId);
            setMenuPosition({ top: rect.bottom + 4, left: rect.left });
        }
    };

    // Close menu when clicking outside or scrolling
    useEffect(() => {
        const handleClickOutside = () => {
            setOpenMenuSessionId(null);
            setMenuPosition(null);
        };
        
        const handleScroll = () => {
            if (openMenuSessionId) {
                setOpenMenuSessionId(null);
                setMenuPosition(null);
            }
        };

        document.addEventListener('click', handleClickOutside);
        const scrollEl = scrollRef.current;
        if (scrollEl) {
            scrollEl.addEventListener('scroll', handleScroll);
        }

        return () => {
            document.removeEventListener('click', handleClickOutside);
            if (scrollEl) {
                scrollEl.removeEventListener('scroll', handleScroll);
            }
        };
    }, [openMenuSessionId]);

    const handleDelete = (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        if (window.confirm(t('confirm_delete'))) {
            onDeleteSession(sessionId);
        }
        setOpenMenuSessionId(null);
        setMenuPosition(null);
    };

    return (
        <div className="contact-list">
            {/* 头部：添加按钮 */}
            <div className="contact-header">
                <button className="new-chat-btn" onClick={onAddContact}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="12" y1="5" x2="12" y2="19"></line>
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    {t('new_chat')}
                </button>
            </div>

            {/* 联系人列表 */}
            <div className="contacts-scroll" ref={scrollRef}>
                {contacts.length === 0 ? (
                    <div className="loading-contacts">
                        <p>{t('no_conversations')}</p>
                    </div>
                ) : (
                    contacts.map(char => (
                        <div key={char.characterId} className="character-group">
                            <div 
                                className="character-header" 
                                onClick={() => toggleChar(char.characterId)}
                            >
                                <div className="char-header-left">
                                    <div className="contact-avatar small">
                                        <img 
                                            src={char.avatarUrl || '/default-avatar.png'} 
                                            alt={char.characterName}
                                            onError={(e) => {
                                                const img = e.target as HTMLImageElement;
                                                img.style.display = 'none';
                                                const fallback = img.nextElementSibling as HTMLElement;
                                                if (fallback) fallback.style.display = 'flex';
                                            }}
                                        />
                                        <span className="avatar-fallback">
                                            {char.characterName.charAt(0)}
                                        </span>
                                    </div>
                                    <span className="char-name">
                                        {char.characterName}
                                    </span>
                                </div>
                                <svg 
                                    className={`chevron ${expandedChars.has(char.characterId) ? 'expanded' : ''}`}
                                    width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                                >
                                    <polyline points="6 9 12 15 18 9"></polyline>
                                </svg>
                            </div>

                            {expandedChars.has(char.characterId) && (
                                <div className="sessions-list">
                                    {char.sessions.map(session => (
                                        <div 
                                            key={session.sessionId}
                                            className={`session-item ${activeSessionId === session.sessionId ? 'active' : ''}`}
                                            onClick={() => onSelectContact(session.sessionId)}
                                        >
                                            <div className="session-info">
                                                <div className="session-preview">
                                                    {session.preview || t('new_conversation_preview')}
                                                </div>
                                            </div>
                                            
                                            <div className="session-actions">
                                                <button 
                                                    className="menu-btn"
                                                    onClick={(e) => toggleMenu(e, session.sessionId)}
                                                >
                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <circle cx="12" cy="12" r="1"></circle>
                                                        <circle cx="19" cy="12" r="1"></circle>
                                                        <circle cx="5" cy="12" r="1"></circle>
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Global Menu Dropdown (Fixed Position) */}
            {openMenuSessionId && menuPosition && (
                <div 
                    className="session-menu-dropdown"
                    style={{ 
                        position: 'fixed', 
                        top: menuPosition.top, 
                        left: menuPosition.left,
                        marginTop: 0,
                        zIndex: 9999
                    }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <button 
                        className="menu-item delete"
                        onClick={(e) => handleDelete(e, openMenuSessionId)}
                    >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2-2h4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        {t('delete_session')}
                    </button>
                </div>
            )}
        </div>
    );
};

