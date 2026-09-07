'use client';

import { useParams } from 'next/navigation';
import GeminiReplicaChatApp from '../../page';

export default function DynamicChatPage() {
  const params = useParams();
  const sessionId = Array.isArray(params?.id) ? params.id[0] : (params?.id as string | undefined);

  return <GeminiReplicaChatApp initialSessionId={sessionId} />;
}