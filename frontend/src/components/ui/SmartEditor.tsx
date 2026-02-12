import React from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableHeader from '@tiptap/extension-table-header';
import TableCell from '@tiptap/extension-table-cell';
import Underline from '@tiptap/extension-underline';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import { Bold, Italic, List, ListOrdered, Quote, Undo, Redo, Table as TableIcon, Link as LinkIcon, Underline as UnderlineIcon } from 'lucide-react';

interface SmartEditorProps {
    content: string;
    onChange: (html: string) => void;
    placeholder?: string;
    className?: string;
    minHeight?: string;
}

export const SmartEditor: React.FC<SmartEditorProps> = ({
    content,
    onChange,
    placeholder = 'Start typing...',
    className = '',
    minHeight = '200px'
}) => {
    const editor = useEditor({
        extensions: [
            StarterKit,
            Underline,
            Link.configure({
                openOnClick: false,
            }),
            Table.configure({
                resizable: true,
            }),
            TableRow,
            TableHeader,
            TableCell,
            Placeholder.configure({
                placeholder,
            }),
        ],
        content: content,
        onUpdate: ({ editor }) => {
            onChange(editor.getHTML());
        },
    });

    if (!editor) {
        return null;
    }

    const MenuBar = () => {
        return (
            <div className="flex flex-wrap gap-1 p-2 border-b border-slate-200/60 bg-slate-50/50">
                <button
                    onClick={() => editor.chain().focus().toggleBold().run()}
                    className={`p-1.5 rounded-md transition-colors ${editor.isActive('bold') ? 'bg-slate-200 text-slate-950' : 'text-slate-500 hover:bg-slate-100'}`}
                    title="Bold"
                >
                    <Bold size={16} />
                </button>
                <button
                    onClick={() => editor.chain().focus().toggleItalic().run()}
                    className={`p-1.5 rounded-md transition-colors ${editor.isActive('italic') ? 'bg-slate-200 text-slate-950' : 'text-slate-500 hover:bg-slate-100'}`}
                    title="Italic"
                >
                    <Italic size={16} />
                </button>
                <button
                    onClick={() => editor.chain().focus().toggleUnderline().run()}
                    className={`p-1.5 rounded-md transition-colors ${editor.isActive('underline') ? 'bg-slate-200 text-slate-950' : 'text-slate-500 hover:bg-slate-100'}`}
                    title="Underline"
                >
                    <UnderlineIcon size={16} />
                </button>
                <div className="w-px h-6 bg-slate-200 mx-1 self-center" />
                <button
                    onClick={() => editor.chain().focus().toggleBulletList().run()}
                    className={`p-1.5 rounded-md transition-colors ${editor.isActive('bulletList') ? 'bg-slate-200 text-slate-950' : 'text-slate-500 hover:bg-slate-100'}`}
                    title="Bullet List"
                >
                    <List size={16} />
                </button>
                <button
                    onClick={() => editor.chain().focus().toggleOrderedList().run()}
                    className={`p-1.5 rounded-md transition-colors ${editor.isActive('orderedList') ? 'bg-slate-200 text-slate-950' : 'text-slate-500 hover:bg-slate-100'}`}
                    title="Ordered List"
                >
                    <ListOrdered size={16} />
                </button>
                <button
                    onClick={() => editor.chain().focus().toggleBlockquote().run()}
                    className={`p-1.5 rounded-md transition-colors ${editor.isActive('blockquote') ? 'bg-slate-200 text-slate-950' : 'text-slate-500 hover:bg-slate-100'}`}
                    title="Quote"
                >
                    <Quote size={16} />
                </button>
                <div className="w-px h-6 bg-slate-200 mx-1 self-center" />
                <button
                    onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
                    className="p-1.5 rounded-md text-slate-500 hover:bg-slate-100 transition-colors"
                    title="Insert Table"
                >
                    <TableIcon size={16} />
                </button>
                <div className="w-px h-6 bg-slate-200 mx-1 self-center" />
                <button
                    onClick={() => editor.chain().focus().undo().run()}
                    disabled={!editor.can().undo()}
                    className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 transition-colors disabled:opacity-30"
                    title="Undo"
                >
                    <Undo size={16} />
                </button>
                <button
                    onClick={() => editor.chain().focus().redo().run()}
                    disabled={!editor.can().redo()}
                    className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 transition-colors disabled:opacity-30"
                    title="Redo"
                >
                    <Redo size={16} />
                </button>
            </div>
        );
    };

    return (
        <div className={`flex flex-col border border-slate-200/60 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-orange-500/20 focus-within:border-orange-500 transition-all ${className}`}>
            <MenuBar />
            <EditorContent
                editor={editor}
                className="tiptap-editor-content overflow-y-auto"
                style={{ minHeight }}
            />
        </div>
    );
};
