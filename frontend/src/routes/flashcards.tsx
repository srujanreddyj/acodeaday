import { useMemo, useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { Brain, AlertCircle, Plus, Save, Trash2, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/api-client'

interface FlashcardItem {
  id: string
  problem_id: string | null
  problem_slug: string | null
  front: string
  back: string
  tags: string[]
  source_url: string | null
  is_active: boolean
  last_reviewed_at: string | null
  next_review_date: string | null
  created_at: string
  updated_at: string
}

interface FlashcardListResponse {
  cards: FlashcardItem[]
  total: number
}

export const Route = createFileRoute('/flashcards')({
  component: FlashcardsPage,
  head: () => ({
    meta: [{ title: 'Flashcards - acodeaday' }],
  }),
})

function FlashcardsPage() {
  const queryClient = useQueryClient()
  const [front, setFront] = useState('')
  const [back, setBack] = useState('')
  const [tagsInput, setTagsInput] = useState('')
  const [problemSlug, setProblemSlug] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [tagFilter, setTagFilter] = useState('')
  const [expandedCardIds, setExpandedCardIds] = useState<Record<string, boolean>>({})

  const { data, isLoading, error } = useQuery({
    queryKey: ['flashcards', 'all'],
    queryFn: () => apiGet<FlashcardListResponse>('/api/flashcards'),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      apiPost<FlashcardItem>('/api/flashcards', {
        front,
        back,
        tags: parseTags(tagsInput),
        problem_slug: problemSlug.trim() || undefined,
        source_url: sourceUrl.trim() || undefined,
      }),
    onSuccess: () => {
      setFront('')
      setBack('')
      setTagsInput('')
      setProblemSlug('')
      setSourceUrl('')
      queryClient.invalidateQueries({ queryKey: ['flashcards'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiDelete(`/api/flashcards/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flashcards'] })
    },
  })

  const reviewMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/flashcards/${id}/review`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flashcards'] })
    },
  })

  const filteredCards = useMemo(() => {
    const cards = data?.cards ?? []
    if (!tagFilter.trim()) return cards
    return cards.filter((card) => card.tags.some((tag) => tag.toLowerCase() === tagFilter.toLowerCase()))
  }, [data?.cards, tagFilter])

  const toggleCard = (cardId: string) => {
    setExpandedCardIds((prev) => ({
      ...prev,
      [cardId]: !prev[cardId],
    }))
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <p className="text-gray-300">Loading flashcards...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 p-6">
        <div className="max-w-2xl mx-auto mt-12 bg-red-500/10 border border-red-500/50 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="text-red-400" size={24} />
            <h2 className="text-xl font-bold text-red-400">Error Loading Flashcards</h2>
          </div>
          <p className="text-gray-300">{(error as Error).message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <Brain className="text-cyan-400" size={30} />
          <h1 className="text-3xl font-black text-white">Flashcards</h1>
          <span className="px-2 py-1 rounded-full bg-cyan-500/20 text-cyan-300 text-sm font-semibold">
            {filteredCards.length}
          </span>
        </div>

        <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-5 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Plus size={18} className="text-cyan-400" />
            Add Flashcard (Independent of solve status)
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <textarea
              rows={4}
              placeholder="Front (question)"
              value={front}
              onChange={(e) => setFront(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white"
            />
            <textarea
              rows={4}
              placeholder="Back (answer / solution)"
              value={back}
              onChange={(e) => setBack(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              type="text"
              placeholder="Tags (comma separated, e.g. dp,array)"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white"
            />
            <input
              type="text"
              placeholder="Problem slug (optional)"
              value={problemSlug}
              onChange={(e) => setProblemSlug(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white"
            />
            <input
              type="url"
              placeholder="Source URL (optional)"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white"
            />
          </div>

          <button
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending || !front.trim() || !back.trim()}
            className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white rounded-lg font-semibold"
          >
            <Save size={16} />
            Save Flashcard
          </button>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="text"
            value={tagFilter}
            onChange={(e) => setTagFilter(e.target.value)}
            placeholder="Filter by exact tag (e.g. dp)"
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white w-full max-w-xs"
          />
        </div>

        {filteredCards.length === 0 ? (
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-8 text-center">
            <p className="text-gray-300 mb-3">No flashcards found.</p>
            <Link to="/" className="text-cyan-400 hover:text-cyan-300">Back to Today&apos;s Practice</Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredCards.map((card) => (
              <div key={card.id} className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    {card.problem_slug ? (
                      <Link
                        to="/problem/$slug"
                        params={{ slug: card.problem_slug }}
                        className="text-cyan-300 font-semibold hover:text-cyan-200"
                      >
                        {card.problem_slug}
                      </Link>
                    ) : (
                      <span className="text-gray-300 font-semibold">Standalone Card</span>
                    )}
                    {card.tags.map((tag) => (
                      <span key={`${card.id}-${tag}`} className="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-xs">
                        {tag}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleCard(card.id)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-200"
                    >
                      {expandedCardIds[card.id] ? (
                        <>
                          <ChevronUp size={15} />
                          Hide
                        </>
                      ) : (
                        <>
                          <ChevronDown size={15} />
                          Show
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => reviewMutation.mutate(card.id)}
                      disabled={reviewMutation.isPending}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-green-600/20 hover:bg-green-600/30 text-green-300"
                    >
                      <CheckCircle2 size={15} />
                      Reviewed
                    </button>
                    <button
                      onClick={() => deleteMutation.mutate(card.id)}
                      disabled={deleteMutation.isPending}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-600/20 hover:bg-red-600/30 text-red-300"
                    >
                      <Trash2 size={15} />
                      Remove
                    </button>
                  </div>
                </div>

                <div className="rounded-lg border border-gray-700 bg-gray-900/50 p-4 mb-3">
                  <p className="text-xs uppercase tracking-wide text-gray-500 mb-2">Question</p>
                  <p
                    className={`text-gray-200 whitespace-pre-wrap ${
                      expandedCardIds[card.id] ? '' : 'max-h-24 overflow-hidden'
                    }`}
                  >
                    {card.front}
                  </p>
                </div>

                {expandedCardIds[card.id] && (
                  <div className="rounded-lg border border-cyan-900/60 bg-cyan-950/20 p-4">
                    <p className="text-xs uppercase tracking-wide text-cyan-400 mb-2">Answer</p>
                    <p className="text-gray-100 whitespace-pre-wrap">{card.back}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function parseTags(value: string): string[] {
  return value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}
