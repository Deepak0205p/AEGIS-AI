import GeminiReplicaChatApp from '../../page';

export function generateStaticParams() {
  return [{ id: 'new' }];
}

export default function DynamicChatPage() {
  return <GeminiReplicaChatApp />;
}