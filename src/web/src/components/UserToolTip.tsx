import React, { ReactNode, useState } from 'react';

interface TooltipProps {
    content: string;
    children: ReactNode;
}

const UserTooltip: React.FC<TooltipProps> = ({ content, children }) => {
    const [visible, setVisible] = useState(false);

    return (
        <div
            className="relative" // 부모 컨테이너에 상대 위치 지정
            onMouseEnter={() => setVisible(true)}
            onMouseLeave={() => setVisible(false)}
            style={{ display: 'inline-block' }}
        >
            {children}
            <div
                style={{
                    position: 'absolute',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    bottom: '100%',
                    marginBottom: '0.5rem',
                    backgroundColor: '#4a5568', // bg-gray-700
                    color: 'white',
                    fontSize: '0.75rem', // text-xs
                    borderRadius: '0.375rem', // rounded-lg
                    padding: '0.25rem 0.5rem', // px-2 py-1
                    whiteSpace: 'nowrap', // whitespace-no-wrap
                    zIndex: 9999, // 툴팁을 충분히 높은 z-index로 설정
                    visibility: visible ? 'visible' : 'hidden',
                    opacity: visible ? 1 : 0,
                    transition: 'opacity 0.2s ease-in-out',
                }}
            >
                {content}
            </div>
        </div>
    );
};

export default UserTooltip;