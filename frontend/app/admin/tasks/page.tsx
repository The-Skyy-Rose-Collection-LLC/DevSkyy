'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { roundTableAutoTrigger } from '@/lib/autonomous/round-table-auto-trigger'
import { Loader2, Trophy, Check, X } from 'lucide-react'

export default function TasksPage() {
  const [prompt, setPrompt] = useState('')
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleSubmitTask = async () => {
    if (!prompt.trim()) return

    setProcessing(true)
    setResult(null)

    const response = await roundTableAutoTrigger.processTask({
      prompt,
      task_type: 'general',
    })

    setResult(response)
    setProcessing(false)

    if (response.success) {
      setPrompt('') // Clear on success
    }
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      <h1 className="font-display text-4xl luxury-text-gradient">
        Autonomous Task Processor
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Submit Task</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter any task... (e.g., 'Write a product description for Black Rose collection')"
            className="min-h-[120px] font-body"
          />

          <Button
            onClick={handleSubmitTask}
            disabled={processing || !prompt.trim()}
            className="w-full"
          >
            {processing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing (Round Table competing...)
              </>
            ) : (
              <>
                <Trophy className="mr-2 h-4 w-4" />
                Submit Task (Auto Round Table + Deploy Winner)
              </>
            )}
          </Button>

          {/* Result Status */}
          {result && (
            <div
              className={`p-4 rounded-lg ${
                result.success
                  ? 'bg-green-500/10 border border-green-500/30'
                  : 'bg-red-500/10 border border-red-500/30'
              }`}
            >
              <div className="flex items-center gap-2">
                {result.success ? (
                  <Check className="h-5 w-5 text-green-400" />
                ) : (
                  <X className="h-5 w-5 text-red-400" />
                )}
                <span className="font-semibold">
                  {result.success ? 'Task Completed Successfully' : 'Task Failed'}
                </span>
              </div>

              {result.success && (
                <div className="mt-3 space-y-2 text-sm">
                  <p>
                    <strong>Winner:</strong>{' '}
                    {result.roundTableResult?.winner?.provider}
                  </p>
                  <p>
                    <strong>Score:</strong>{' '}
                    {result.roundTableResult?.winner?.score?.toFixed(2)}
                  </p>
                  {result.wordpressPostId && (
                    <a
                      href={`${process.env.NEXT_PUBLIC_WORDPRESS_URL}/wp-admin/post.php?post=${result.wordpressPostId}&action=edit`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-green-400 hover:underline block"
                    >
                      View Published WordPress Post →
                    </a>
                  )}
                </div>
              )}

              {result.error && (
                <p className="mt-2 text-sm text-red-400">{result.error}</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
