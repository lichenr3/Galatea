import React, { useState, useEffect } from 'react';
import { getAvailableCharacters } from '../../../services/sessionService';
import { useLanguage } from '../../../i18n/LanguageContext';
import type { CharacterInfo } from '../../../types';
import './AddContactModal.css';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    onSelectCharacter: (characterId: string) => void;
}

export const AddContactModal: React.FC<Props> = ({ isOpen, onClose, onSelectCharacter }) => {
    const { language, t } = useLanguage();
    const [characters, setCharacters] = useState<CharacterInfo[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            loadCharacters();
        }
    }, [isOpen]);

    const loadCharacters = async () => {
        setLoading(true);
        try {
            const chars = await getAvailableCharacters(language);
            setCharacters(chars);
            if (chars.length > 0) {
                setSelectedCharacter(chars[0].id);
            }
        } catch (err) {
            console.error('加载角色列表失败:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleConfirm = () => {
        if (selectedCharacter) {
            onSelectCharacter(selectedCharacter);
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{t('modal_title')}</h2>
                    <button className="modal-close" onClick={onClose}>×</button>
                </div>

                <div className="modal-body">
                    {loading ? (
                        <div className="loading">{t('loading')}</div>
                    ) : (
                        <div className="character-list">
                            {characters.map(char => {
                                const isSelected = selectedCharacter === char.id;
                                const description = char.description[language as 'zh' | 'en'] || char.description.zh || char.description.en;
                                const characterName = char.name[language as 'zh' | 'en'] || char.name.zh || char.name.en;
                                
                                return (
                                    <div 
                                        key={char.id}
                                        className={`character-card ${isSelected ? 'selected' : ''}`}
                                        onClick={() => setSelectedCharacter(char.id)}
                                    >
                                        <div className="character-card-background"></div>
                                        
                                        <div className="character-card-content">
                                            <div className="character-avatar">
                                                {/* 总是渲染首字母作为备用 */}
                                                <div className="avatar-circle">
                                                    <span className="avatar-text">
                                                        {characterName.charAt(0)}
                                                    </span>
                                                </div>
                                                
                                                {/* 如果有头像URL，在上面覆盖一层图片 */}
                                                {char.avatarUrl && (
                                                    <img 
                                                        src={char.avatarUrl} 
                                                        alt={characterName}
                                                        className="avatar-image"
                                                        onError={(e) => {
                                                            // 图片加载失败时隐藏图片，显示下面的首字母
                                                            e.currentTarget.style.display = 'none';
                                                        }}
                                                    />
                                                )}
                                                
                                                <div className="avatar-glow"></div>
                                            </div>
                                            
                                            <div className="character-info">
                                                <div className="character-name">
                                                    {characterName}
                                                </div>
                                                <div className="character-desc">
                                                    {description || t('start_new_chat')}
                                                </div>
                                            </div>
                                            
                                            <div className="character-card-indicator">
                                                {isSelected && (
                                                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                                        <circle cx="10" cy="10" r="9" fill="currentColor" opacity="0.2"/>
                                                        <path d="M6 10l3 3 5-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                                    </svg>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                <div className="modal-footer">
                    <button className="btn-cancel" onClick={onClose}>{t('cancel')}</button>
                    <button 
                        className="btn-confirm" 
                        onClick={handleConfirm}
                        disabled={!selectedCharacter}
                    >
                        {t('confirm')}
                    </button>
                </div>
            </div>
        </div>
    );
};

