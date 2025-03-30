// src/components/VideoProcessing.tsx
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Progress } from '~/components/ui/progress'
import { Badge } from '~/components/ui/badge'
import { Loader2 } from 'lucide-react'

interface VideoProcessingProps {
  taskId: string
}

export function VideoProcessing({ taskId }: VideoProcessingProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['processingStatus', taskId],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8000/api/status/${taskId}`)
      return response.json()
    },
    refetchInterval: (data) => {
      return data?.status === 'completed' ? false : 2000
    },
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Processing Status
          <Badge variant={data?.status === 'completed' ? 'success' : 'secondary'}>
            {data?.status || 'Processing'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : (
          <div className="space-y-4">
            <Progress value={data?.progress || 0} />
            <div className="grid gap-4">
              {data?.steps?.map((step: any) => (
                <div
                  key={step.name}
                  className="flex items-center justify-between"
                >
                  <span>{step.name}</span>
                  <Badge>{step.status}</Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}