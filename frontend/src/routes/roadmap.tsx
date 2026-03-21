import { useMemo, useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  AlertCircle,
  BookOpen,
  Brain,
  ChevronDown,
  ChevronUp,
  Code2,
  ExternalLink,
  Map,
  Plus,
  X,
} from 'lucide-react'

import { apiGet, apiPost, apiPut } from '@/lib/api-client'

interface RoadmapLegendCounts {
  easy: number
  med: number
  hard: number
}

interface RoadmapNodeSummary {
  slug: string
  title: string
  difficulty: 'easy' | 'med' | 'hard'
  x: number
  y: number
  width: number
  height: number
  completed_count: number
  total_count: number
}

interface RoadmapEdge {
  source_node_slug: string
  target_node_slug: string
}

interface RoadmapOverview {
  slug: string
  title: string
  description: string | null
  total_problem_goal: number
  completed_problem_count: number
  total_problem_count: number
  legend_counts: RoadmapLegendCounts
  nodes: RoadmapNodeSummary[]
  edges: RoadmapEdge[]
}

interface TutorialItem {
  id: string
  title: string
  body: string | null
  resource_url: string | null
  completed: boolean
}

interface TemplateItem {
  id: string
  title: string
  body: string | null
  code_language: string | null
  completed: boolean
}

interface TemplateGroup {
  key: string
  title: string
  items: TemplateItem[]
}

interface PracticeItem {
  problem_id: string
  slug: string
  title: string
  difficulty: 'easy' | 'medium' | 'hard'
  source_url: string | null
  completed: boolean
  has_personal_solution: boolean
}

interface FlashcardItem {
  id: string
  front: string
  back: string
  tags: string[]
  problem_slug: string | null
  source_url: string | null
  last_reviewed_at: string | null
}

interface NodeDetail {
  roadmap_slug: string
  node_slug: string
  title: string
  description: string | null
  difficulty: 'easy' | 'med' | 'hard'
  completed_count: number
  total_count: number
  tutorials: TutorialItem[]
  template_groups: TemplateGroup[]
  practice: PracticeItem[]
  flashcards: FlashcardItem[]
}

export const Route = createFileRoute('/roadmap')({
  component: RoadmapPage,
  head: () => ({
    meta: [{ title: 'Roadmap - acodeaday' }],
  }),
})

function RoadmapPage() {
  const queryClient = useQueryClient()
  const [selectedNodeSlug, setSelectedNodeSlug] = useState<string | null>(null)
  const [expandedTemplates, setExpandedTemplates] = useState<Record<string, boolean>>({})
  const [front, setFront] = useState('')
  const [back, setBack] = useState('')
  const [tagsInput, setTagsInput] = useState('')

  const roadmapQuery = useQuery({
    queryKey: ['roadmap', 'dsa-roadmap'],
    queryFn: () => apiGet<RoadmapOverview>('/api/roadmaps/dsa-roadmap'),
  })

  const nodeDetailQuery = useQuery({
    queryKey: ['roadmap', 'dsa-roadmap', 'node', selectedNodeSlug],
    queryFn: () => apiGet<NodeDetail>(`/api/roadmaps/dsa-roadmap/nodes/${selectedNodeSlug}`),
    enabled: Boolean(selectedNodeSlug),
  })

  const completeItemMutation = useMutation({
    mutationFn: ({ itemId, completed }: { itemId: string; completed: boolean }) =>
      apiPut(`/api/roadmaps/items/${itemId}/completion`, { completed }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmap', 'dsa-roadmap'] })
      queryClient.invalidateQueries({ queryKey: ['roadmap', 'dsa-roadmap', 'node', selectedNodeSlug] })
    },
  })

  const createFlashcardMutation = useMutation({
    mutationFn: () =>
      apiPost('/api/flashcards', {
        front,
        back,
        tags: parseTags(tagsInput),
        roadmap_node_slugs: selectedNodeSlug ? [selectedNodeSlug] : [],
      }),
    onSuccess: () => {
      setFront('')
      setBack('')
      setTagsInput('')
      queryClient.invalidateQueries({ queryKey: ['roadmap', 'dsa-roadmap', 'node', selectedNodeSlug] })
    },
  })

  const edgeLines = useMemo(() => {
    if (!roadmapQuery.data) return []
    const nodeMap = new Map(roadmapQuery.data.nodes.map((node) => [node.slug, node]))
    return roadmapQuery.data.edges
      .map((edge) => {
        const source = nodeMap.get(edge.source_node_slug)
        const target = nodeMap.get(edge.target_node_slug)
        if (!source || !target) return null
        return {
          key: `${edge.source_node_slug}-${edge.target_node_slug}`,
          x1: source.x + source.width / 2,
          y1: source.y + source.height,
          x2: target.x + target.width / 2,
          y2: target.y,
        }
      })
      .filter(Boolean) as Array<{ key: string; x1: number; y1: number; x2: number; y2: number }>
  }, [roadmapQuery.data])

  if (roadmapQuery.isLoading) {
    return (
      <PageShell>
        <CenteredMessage text="Loading roadmap..." />
      </PageShell>
    )
  }

  if (roadmapQuery.error || !roadmapQuery.data) {
    return (
      <PageShell>
        <ErrorMessage message={(roadmapQuery.error as Error)?.message || 'Failed to load roadmap.'} />
      </PageShell>
    )
  }

  const roadmap = roadmapQuery.data
  const panelOpen = Boolean(selectedNodeSlug)

  return (
    <div className="min-h-screen bg-[#111215] text-white">
      <div className="flex min-h-[calc(100vh-72px)]">
        <aside className="w-[280px] shrink-0 border-r border-white/10 bg-[#16181d] p-6">
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5 shadow-2xl shadow-black/20">
            <div className="mb-5 flex items-center gap-2 text-sm text-orange-300">
              <Map size={16} />
              <span>Covers your personal DSA roadmap</span>
            </div>

            <div className="mb-5 flex items-center justify-between">
              <div className="space-y-3 text-lg">
                <LegendRow color="bg-emerald-500" label="Easy" count={roadmap.legend_counts.easy} />
                <LegendRow color="bg-amber-400" label="Med" count={roadmap.legend_counts.med} />
                <LegendRow color="bg-red-500" label="Hard" count={roadmap.legend_counts.hard} />
              </div>

              <div className="flex h-28 w-28 items-center justify-center rounded-full border-8 border-amber-700/40 text-center">
                <div>
                  <div className="text-3xl font-black">{roadmap.completed_problem_count}</div>
                  <div className="text-sm text-gray-400">/{roadmap.total_problem_goal}</div>
                </div>
              </div>
            </div>

            <div className="border-t border-white/10 pt-4 text-sm text-gray-300">
              <p>{roadmap.title}</p>
              <p className="mt-2 text-gray-500">
                {roadmap.completed_problem_count} solved links across {roadmap.total_problem_count} mapped problems.
              </p>
            </div>
          </div>
        </aside>

        <main className="relative flex-1 overflow-auto bg-[#121317]">
          <div className="relative min-h-[1200px] min-w-[1700px] p-8">
            <svg className="pointer-events-none absolute inset-0 h-full w-full">
              {edgeLines.map((line) => (
                <path
                  key={line.key}
                  d={`M ${line.x1} ${line.y1} C ${line.x1} ${(line.y1 + line.y2) / 2}, ${line.x2} ${(line.y1 + line.y2) / 2}, ${line.x2} ${line.y2}`}
                  fill="none"
                  stroke="rgba(255,255,255,0.35)"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              ))}
            </svg>

            {roadmap.nodes.map((node) => (
              <button
                key={node.slug}
                onClick={() => setSelectedNodeSlug(node.slug)}
                className={`absolute rounded-3xl border bg-[#1a1c21] p-4 text-left shadow-xl transition ${selectedNodeSlug === node.slug ? 'border-cyan-400 shadow-cyan-950/40' : 'border-white/10 hover:border-white/20'}`}
                style={{ left: node.x, top: node.y, width: node.width, minHeight: node.height }}
              >
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div className="text-xl font-bold leading-tight text-white">{node.title}</div>
                  <span className={`mt-1 h-3.5 w-3.5 rounded-full ${difficultyColor(node.difficulty)}`} />
                </div>
                <div className="h-1.5 rounded-full bg-white/10">
                  <div
                    className="h-1.5 rounded-full bg-white/50"
                    style={{ width: `${node.total_count === 0 ? 0 : (node.completed_count / node.total_count) * 100}%` }}
                  />
                </div>
                <div className="mt-2 text-sm text-gray-400">{node.completed_count}/{node.total_count}</div>
              </button>
            ))}
          </div>
        </main>

        {panelOpen && (
          <aside className="w-[520px] shrink-0 border-l border-white/10 bg-[#17181c]">
            {nodeDetailQuery.isLoading || !nodeDetailQuery.data ? (
              <div className="p-8 text-gray-300">Loading node details...</div>
            ) : (
              <div className="flex h-full flex-col">
                <div className="flex items-center justify-between border-b border-white/10 p-6">
                  <div>
                    <h2 className="text-4xl font-black">{nodeDetailQuery.data.title}</h2>
                    <div className="mt-3 flex items-center gap-3 text-gray-400">
                      <div className="h-2 w-28 rounded-full bg-white/10">
                        <div
                          className="h-2 rounded-full bg-white/50"
                          style={{ width: `${nodeDetailQuery.data.total_count === 0 ? 0 : (nodeDetailQuery.data.completed_count / nodeDetailQuery.data.total_count) * 100}%` }}
                        />
                      </div>
                      <span>{nodeDetailQuery.data.completed_count}/{nodeDetailQuery.data.total_count}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedNodeSlug(null)}
                    className="rounded-xl p-2 text-gray-400 hover:bg-white/5 hover:text-white"
                  >
                    <X size={24} />
                  </button>
                </div>

                <div className="flex-1 space-y-8 overflow-y-auto p-6">
                  <PanelSection title="Tutorial" icon={<BookOpen size={18} />}>
                    {nodeDetailQuery.data.tutorials.length === 0 ? (
                      <EmptyState text="No tutorial content linked yet." />
                    ) : (
                      <div className="space-y-4">
                        {nodeDetailQuery.data.tutorials.map((item) => (
                          <div key={item.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                            <label className="mb-3 flex items-center gap-3 text-lg font-semibold">
                              <input
                                type="checkbox"
                                checked={item.completed}
                                onChange={(e) =>
                                  completeItemMutation.mutate({ itemId: item.id, completed: e.target.checked })
                                }
                                className="h-5 w-5 rounded border-white/20 bg-transparent"
                              />
                              <span>{item.title}</span>
                            </label>
                            {item.body && <MarkdownBlock content={item.body} />}
                            {item.resource_url && (
                              <a
                                href={item.resource_url}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-3 inline-flex items-center gap-2 text-cyan-300 hover:text-cyan-200"
                              >
                                Open resource <ExternalLink size={14} />
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </PanelSection>

                  <PanelSection title="Code Templates" icon={<Code2 size={18} />}>
                    {nodeDetailQuery.data.template_groups.length === 0 ? (
                      <EmptyState text="No templates linked yet." />
                    ) : (
                      <div className="space-y-3">
                        {nodeDetailQuery.data.template_groups.map((group) => {
                          const expanded = expandedTemplates[group.key] ?? group.items.length === 1
                          return (
                            <div key={group.key} className="rounded-2xl border border-white/10 bg-white/[0.03]">
                              <button
                                onClick={() =>
                                  setExpandedTemplates((prev) => ({ ...prev, [group.key]: !expanded }))
                                }
                                className="flex w-full items-center justify-between px-4 py-4 text-left"
                              >
                                <div className="font-semibold">{group.title}</div>
                                {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                              </button>
                              {expanded && (
                                <div className="space-y-4 border-t border-white/10 px-4 py-4">
                                  {group.items.map((item) => (
                                    <div key={item.id} className="rounded-xl border border-white/10 bg-black/10 p-4">
                                      <label className="mb-3 flex items-center gap-3 text-sm font-medium text-gray-300">
                                        <input
                                          type="checkbox"
                                          checked={item.completed}
                                          onChange={(e) =>
                                            completeItemMutation.mutate({
                                              itemId: item.id,
                                              completed: e.target.checked,
                                            })
                                          }
                                          className="h-4 w-4 rounded border-white/20 bg-transparent"
                                        />
                                        <span>{item.title}</span>
                                      </label>
                                      {item.body && <MarkdownBlock content={item.body} />}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </PanelSection>

                  <PanelSection title="Practice Problems" icon={<AlertCircle size={18} />}>
                    {nodeDetailQuery.data.practice.length === 0 ? (
                      <EmptyState text="No mapped problems yet. Use the CSV importer to attach them." />
                    ) : (
                      <div className="overflow-hidden rounded-2xl border border-white/10">
                        <table className="w-full text-left text-sm">
                          <thead className="bg-white/[0.03] text-gray-400">
                            <tr>
                              <th className="px-4 py-3">Status</th>
                              <th className="px-4 py-3">Problem</th>
                              <th className="px-4 py-3">Notes</th>
                            </tr>
                          </thead>
                          <tbody>
                            {nodeDetailQuery.data.practice.map((item) => (
                              <tr key={item.problem_id} className="border-t border-white/10">
                                <td className="px-4 py-3">
                                  <span
                                    className={`inline-block h-3.5 w-3.5 rounded-full ${item.completed ? 'bg-emerald-400' : difficultyColor(item.difficulty === 'medium' ? 'med' : item.difficulty)}`}
                                  />
                                </td>
                                <td className="px-4 py-3">
                                  <Link
                                    to="/problem/$slug"
                                    params={{ slug: item.slug }}
                                    className="font-medium text-white hover:text-cyan-300"
                                  >
                                    {item.title}
                                  </Link>
                                </td>
                                <td className="px-4 py-3 text-right text-gray-400">
                                  {item.has_personal_solution ? 'Saved' : 'None'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </PanelSection>

                  <PanelSection title="Flashcards" icon={<Brain size={18} />}>
                    <div className="space-y-4">
                      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-cyan-300">
                          <Plus size={16} />
                          Add flashcard to this topic
                        </div>
                        <div className="space-y-3">
                          <textarea
                            value={front}
                            onChange={(e) => setFront(e.target.value)}
                            rows={3}
                            placeholder="Front / question"
                            className="w-full rounded-xl border border-white/10 bg-[#101216] px-3 py-2 text-white"
                          />
                          <textarea
                            value={back}
                            onChange={(e) => setBack(e.target.value)}
                            rows={4}
                            placeholder="Back / answer"
                            className="w-full rounded-xl border border-white/10 bg-[#101216] px-3 py-2 text-white"
                          />
                          <input
                            value={tagsInput}
                            onChange={(e) => setTagsInput(e.target.value)}
                            placeholder="Tags (comma separated)"
                            className="w-full rounded-xl border border-white/10 bg-[#101216] px-3 py-2 text-white"
                          />
                          <button
                            onClick={() => createFlashcardMutation.mutate()}
                            disabled={createFlashcardMutation.isPending || !front.trim() || !back.trim()}
                            className="rounded-xl bg-cyan-600 px-4 py-2 font-semibold text-white disabled:opacity-50"
                          >
                            Save flashcard
                          </button>
                        </div>
                      </div>

                      {nodeDetailQuery.data.flashcards.length === 0 ? (
                        <EmptyState text="No flashcards linked to this node yet." />
                      ) : (
                        <div className="space-y-3">
                          {nodeDetailQuery.data.flashcards.map((card) => (
                            <div key={card.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                              <div className="mb-2 flex flex-wrap items-center gap-2">
                                {card.tags.map((tag) => (
                                  <span
                                    key={`${card.id}-${tag}`}
                                    className="rounded-full bg-cyan-500/15 px-2 py-0.5 text-xs text-cyan-200"
                                  >
                                    {tag}
                                  </span>
                                ))}
                                {card.problem_slug && (
                                  <Link
                                    to="/problem/$slug"
                                    params={{ slug: card.problem_slug }}
                                    className="text-xs text-gray-400 hover:text-cyan-300"
                                  >
                                    {card.problem_slug}
                                  </Link>
                                )}
                              </div>
                              <div className="mb-2 text-sm uppercase tracking-[0.18em] text-cyan-300">Question</div>
                              <div className="mb-4 whitespace-pre-wrap text-gray-100">{card.front}</div>
                              <div className="mb-2 text-sm uppercase tracking-[0.18em] text-cyan-300">Answer</div>
                              <div className="whitespace-pre-wrap text-gray-300">{card.back}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </PanelSection>
                </div>
              </div>
            )}
          </aside>
        )}
      </div>
    </div>
  )
}

function difficultyColor(difficulty: 'easy' | 'med' | 'hard') {
  if (difficulty === 'easy') return 'bg-emerald-500'
  if (difficulty === 'med') return 'bg-amber-400'
  return 'bg-red-500'
}

function parseTags(input: string) {
  return input
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}

function MarkdownBlock({ content }: { content: string }) {
  return (
    <div className="prose prose-invert max-w-none prose-pre:bg-[#101216] prose-pre:border prose-pre:border-white/10">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}

function PanelSection({
  title,
  icon,
  children,
}: {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section>
      <div className="mb-4 flex items-center gap-2 text-3xl font-bold">
        {icon}
        <h3>{title}</h3>
      </div>
      {children}
    </section>
  )
}

function LegendRow({ color, label, count }: { color: string; label: string; count: number }) {
  return (
    <div className="flex items-center gap-3 text-gray-300">
      <span className={`h-4 w-4 rounded-full ${color}`} />
      <span>{label}</span>
      <span className="ml-auto text-gray-500">{count}</span>
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-2xl border border-dashed border-white/10 p-5 text-gray-400">{text}</div>
}

function PageShell({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-[#111215] text-white">{children}</div>
}

function CenteredMessage({ text }: { text: string }) {
  return <div className="flex min-h-screen items-center justify-center text-gray-300">{text}</div>
}

function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="mx-auto max-w-2xl p-8">
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-red-200">{message}</div>
    </div>
  )
}
