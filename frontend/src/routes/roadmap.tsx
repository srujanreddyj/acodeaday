import { type PointerEvent as ReactPointerEvent, type ReactNode, useEffect, useMemo, useRef, useState } from 'react'
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
  Flame,
  Maximize2,
  Minus,
  Plus,
  Scan,
  Search,
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

interface ViewportState {
  scale: number
  offsetX: number
  offsetY: number
}

type EdgeSide = 'top' | 'right' | 'bottom' | 'left'

interface EdgePortConfig {
  side: EdgeSide
  offset?: number
}

interface EdgeGeometry {
  key: string
  d: string
}

interface CanvasBounds {
  minX: number
  minY: number
  width: number
  height: number
}

const CANVAS_PADDING = 150
const OVERVIEW_CARD_WIDTH = 278
const OVERVIEW_CARD_OFFSET = 32
const CANVAS_LEFT_RESERVE = OVERVIEW_CARD_WIDTH + OVERVIEW_CARD_OFFSET + 44
const MIN_SCALE = 0.45
const MAX_SCALE = 1.4
const GROUP_NODE_SLUGS = new Set([
  'operations',
  'basic-data-structure',
  'array-two-pointer',
  'advanced-data-structure',
  'other',
  'traverse-view',
  'subproblem-view',
])

const GROUP_CHILDREN: Record<string, string[]> = {
  operations: ['prefix-sum', 'diff-array', 'two-d-array'],
  'basic-data-structure': ['cycle-array', 'stack-and-queue', 'hashing', 'design'],
  'array-two-pointer': ['two-pointer', 'sliding-window', 'binary-search', 'randomize'],
  'advanced-data-structure': ['bst', 'heap', 'trie', 'graph'],
  other: ['math', 'greedy'],
  'traverse-view': ['backtracking', 'dfs'],
  'subproblem-view': ['divide-and-conquer', 'dp'],
}

const GROUPED_CHILD_SLUGS = new Set(Object.values(GROUP_CHILDREN).flat())
const MIN_GROUP_HEIGHT = 170
const GROUP_BOTTOM_PADDING = 22
const GROUP_RIGHT_PADDING = 18

const EDGE_PORTS: Record<string, { source: EdgePortConfig; target: EdgePortConfig }> = {
  'data-structure-and-algorithm-array': { source: { side: 'bottom', offset: 0.42 }, target: { side: 'top', offset: 0.52 } },
  'data-structure-and-algorithm-linked-list': { source: { side: 'bottom', offset: 0.58 }, target: { side: 'top', offset: 0.5 } },
  'array-operations': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.52 } },
  'operations-basic-data-structure': { source: { side: 'right', offset: 0.52 }, target: { side: 'left', offset: 0.5 } },
  'operations-array-two-pointer': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.5 } },
  'linked-list-basic-data-structure': { source: { side: 'bottom', offset: 0.35 }, target: { side: 'top', offset: 0.52 } },
  'linked-list-two-pointer-linked-list': { source: { side: 'bottom', offset: 0.62 }, target: { side: 'top', offset: 0.5 } },
  'two-pointer-linked-list-recursion': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.5 } },
  'recursion-binary-tree': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.5 } },
  'binary-tree-advanced-data-structure': { source: { side: 'left', offset: 0.45 }, target: { side: 'right', offset: 0.56 } },
  'binary-tree-recursive-traverse': { source: { side: 'bottom', offset: 0.34 }, target: { side: 'top', offset: 0.5 } },
  'binary-tree-level-traverse': { source: { side: 'bottom', offset: 0.72 }, target: { side: 'top', offset: 0.5 } },
  'recursive-traverse-traverse-view': { source: { side: 'bottom', offset: 0.3 }, target: { side: 'top', offset: 0.5 } },
  'recursive-traverse-subproblem-view': { source: { side: 'bottom', offset: 0.72 }, target: { side: 'top', offset: 0.5 } },
  'traverse-view-backtracking': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.5 } },
  'traverse-view-dfs': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.5 } },
  'subproblem-view-divide-and-conquer': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.5 } },
  'subproblem-view-dp': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.5 } },
  'level-traverse-bfs': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.5 } },
  'bfs-shortest-path': { source: { side: 'bottom', offset: 0.5 }, target: { side: 'top', offset: 0.5 } },
}

export const Route = createFileRoute('/roadmap')({
  component: RoadmapPage,
  head: () => ({
    meta: [{ title: 'Roadmap - acodeaday' }],
  }),
})

function RoadmapPage() {
  const queryClient = useQueryClient()
  const viewportRef = useRef<HTMLDivElement | null>(null)
  const dragOriginRef = useRef<{ x: number; y: number } | null>(null)
  const [selectedNodeSlug, setSelectedNodeSlug] = useState<string | null>(null)
  const [expandedTemplates, setExpandedTemplates] = useState<Record<string, boolean>>({})
  const [front, setFront] = useState('')
  const [back, setBack] = useState('')
  const [tagsInput, setTagsInput] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [viewport, setViewport] = useState<ViewportState>({ scale: 1, offsetX: 0, offsetY: 0 })

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

  const displayNodeMap = useMemo(() => {
    const nodes = roadmapQuery.data?.nodes ?? []
    const map = new Map(
      nodes.map((node) => [
        node.slug,
        {
          ...node,
        },
      ]),
    )

    for (const groupSlug of GROUP_NODE_SLUGS) {
      const groupNode = map.get(groupSlug)
      const childSlugs = GROUP_CHILDREN[groupSlug]
      if (!groupNode || !childSlugs?.length) continue

      const childNodes = childSlugs
        .map((slug) => map.get(slug))
        .filter((node): node is RoadmapNodeSummary => Boolean(node))

      if (childNodes.length === 0) continue

      const maxRight = Math.max(...childNodes.map((child) => child.x - groupNode.x + child.width))
      const maxBottom = Math.max(...childNodes.map((child) => child.y - groupNode.y + child.height))

      map.set(groupSlug, {
        ...groupNode,
        width: Math.max(groupNode.width, Math.ceil(maxRight + GROUP_RIGHT_PADDING)),
        height: Math.max(MIN_GROUP_HEIGHT, Math.ceil(maxBottom + GROUP_BOTTOM_PADDING)),
      })
    }

    return map
  }, [roadmapQuery.data])

  const displayNodes = useMemo(() => {
    const nodes = roadmapQuery.data?.nodes ?? []
    return nodes.map((node) => displayNodeMap.get(node.slug) ?? node)
  }, [displayNodeMap, roadmapQuery.data])

  const canvasBounds = useMemo<CanvasBounds>(() => {
    if (displayNodes.length === 0) {
      return { minX: 0, minY: 0, width: 1700, height: 1300 }
    }

    const minX = Math.min(...displayNodes.map((node) => node.x))
    const minY = Math.min(...displayNodes.map((node) => node.y))
    const maxX = Math.max(...displayNodes.map((node) => node.x + node.width))
    const maxY = Math.max(...displayNodes.map((node) => node.y + node.height))

    return {
      minX,
      minY,
      width: maxX - minX + CANVAS_PADDING * 2,
      height: maxY - minY + CANVAS_PADDING * 2,
    }
  }, [displayNodes])

  const edgeLines = useMemo(() => {
    if (!roadmapQuery.data) return []
    return roadmapQuery.data.edges
      .filter((edge) => !GROUPED_CHILD_SLUGS.has(edge.source_node_slug) && !GROUPED_CHILD_SLUGS.has(edge.target_node_slug))
      .map((edge) => {
        const source = displayNodeMap.get(edge.source_node_slug)
        const target = displayNodeMap.get(edge.target_node_slug)
        if (!source || !target) return null
        const key = `${edge.source_node_slug}-${edge.target_node_slug}`
        const config = EDGE_PORTS[key]
        const sourcePoint = getNodeAnchor(source, config?.source?.side ?? 'bottom', config?.source?.offset ?? 0.5, canvasBounds)
        const targetPoint = getNodeAnchor(target, config?.target?.side ?? 'top', config?.target?.offset ?? 0.5, canvasBounds)
        return {
          key,
          d: buildEdgePath(sourcePoint, targetPoint, config?.source?.side ?? 'bottom', config?.target?.side ?? 'top'),
        }
      })
      .filter(Boolean) as EdgeGeometry[]
  }, [canvasBounds.minX, canvasBounds.minY, displayNodeMap, roadmapQuery.data])

  const fitToScreen = () => {
    if (!viewportRef.current) return
    const width = viewportRef.current.clientWidth
    const height = viewportRef.current.clientHeight
    if (width === 0 || height === 0) return

    const usableWidth = Math.max(width - CANVAS_LEFT_RESERVE, width * 0.56)
    const scale = clamp(Math.min(usableWidth / canvasBounds.width, (height - 24) / canvasBounds.height), MIN_SCALE, 1.06)
    const offsetX = CANVAS_LEFT_RESERVE + (usableWidth - canvasBounds.width * scale) / 2
    const offsetY = Math.max(20, (height - canvasBounds.height * scale) / 2 - 26)
    setViewport({
      scale,
      offsetX,
      offsetY,
    })
  }

  useEffect(() => {
    if (!roadmapQuery.data || !viewportRef.current) return
    fitToScreen()
    window.addEventListener('resize', fitToScreen)
    return () => window.removeEventListener('resize', fitToScreen)
  }, [canvasBounds.height, canvasBounds.width, roadmapQuery.data])

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
  const groupNodes = displayNodes.filter((node) => GROUP_NODE_SLUGS.has(node.slug))
  const topicNodeMap = displayNodeMap
  const topicNodes = displayNodes.filter(
    (node) => !GROUP_NODE_SLUGS.has(node.slug) && !GROUPED_CHILD_SLUGS.has(node.slug),
  )
  const panelOpen = Boolean(selectedNodeSlug)

  const applyZoom = (delta: number) => {
    setViewport((current) => ({
      ...current,
      scale: clamp(current.scale + delta, MIN_SCALE, MAX_SCALE),
    }))
  }

  const applyPan = (dx: number, dy: number) => {
    setViewport((current) => ({
      ...current,
      offsetX: current.offsetX + dx,
      offsetY: current.offsetY + dy,
    }))
  }

  const beginDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return
    const target = event.target as HTMLElement | null
    if (target?.closest('button, a, input, textarea, label')) return
    dragOriginRef.current = { x: event.clientX, y: event.clientY }
    setIsDragging(true)
  }

  const updateDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!dragOriginRef.current) return
    const dx = event.clientX - dragOriginRef.current.x
    const dy = event.clientY - dragOriginRef.current.y
    dragOriginRef.current = { x: event.clientX, y: event.clientY }
    applyPan(dx, dy)
  }

  const endDrag = () => {
    dragOriginRef.current = null
    setIsDragging(false)
  }

  return (
    <PageShell>
      <div className="h-[calc(100vh-81px)] bg-[#16171c] p-4">
        <div className="relative h-full overflow-hidden rounded-[30px] border border-white/6 bg-[#1b1c21] shadow-[inset_0_1px_0_rgba(255,255,255,0.02),0_26px_80px_rgba(0,0,0,0.34)]">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.04),transparent_40%)]" />

          <div className="absolute left-8 top-8 z-30 w-[278px]">
          <RoadmapOverviewCard
            roadmap={roadmap}
            onZoomIn={() => applyZoom(0.1)}
            onZoomOut={() => applyZoom(-0.1)}
            onFit={fitToScreen}
          />
        </div>

          <div
            ref={viewportRef}
          className={`relative h-full overflow-hidden ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
          onPointerDown={beginDrag}
          onPointerMove={updateDrag}
          onPointerUp={endDrag}
          onPointerLeave={endDrag}
          >
            <div
            className="absolute left-0 top-0 origin-top-left transition-transform duration-200 ease-out"
            style={{
              width: canvasBounds.width,
              height: canvasBounds.height,
              transform: `translate(${viewport.offsetX}px, ${viewport.offsetY}px) scale(${viewport.scale})`,
            }}
          >
              <svg className="pointer-events-none absolute inset-0 h-full w-full">
              {edgeLines.map((line) => (
                <path
                  key={line.key}
                  d={line.d}
                  fill="none"
                  stroke="rgba(230,231,236,0.52)"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              ))}
            </svg>

              {groupNodes.map((node) => (
              <GroupNodeCard
                key={node.slug}
                node={node}
                childrenSlugs={GROUP_CHILDREN[node.slug] ?? []}
                topicNodeMap={topicNodeMap}
                selectedNodeSlug={selectedNodeSlug}
                onSelect={setSelectedNodeSlug}
                canvasBounds={canvasBounds}
              />
            ))}

              {topicNodes.map((node) => (
              <RoadmapNodeCard
                key={node.slug}
                node={node}
                selected={selectedNodeSlug === node.slug}
                onClick={() => setSelectedNodeSlug(node.slug)}
                canvasBounds={canvasBounds}
                largeTitle={node.slug === 'data-structure-and-algorithm'}
              />
            ))}
            </div>
          </div>

            {panelOpen && (
            <>
              <div className="absolute inset-0 z-30 bg-black/28 backdrop-blur-[1px]" />
              <aside className="absolute inset-y-0 right-0 z-40 w-[560px] border-l border-white/10 bg-[#17181c]/98 shadow-2xl shadow-black/40 backdrop-blur-xl">
            {nodeDetailQuery.isLoading || !nodeDetailQuery.data ? (
              <div className="p-8 text-gray-300">Loading node details...</div>
            ) : (
              <div className="flex h-full flex-col">
                <div className="flex items-center justify-between border-b border-white/10 p-6">
                  <div>
                    <h2 className="text-4xl font-black tracking-tight text-white">{nodeDetailQuery.data.title}</h2>
                    <div className="mt-3 flex items-center gap-3 text-gray-400">
                      <div className="h-2 w-28 rounded-full bg-white/10">
                        <div
                          className="h-2 rounded-full bg-white/50"
                          style={{
                            width: `${nodeDetailQuery.data.total_count === 0 ? 0 : (nodeDetailQuery.data.completed_count / nodeDetailQuery.data.total_count) * 100}%`,
                          }}
                        />
                      </div>
                      <span>
                        {nodeDetailQuery.data.completed_count}/{nodeDetailQuery.data.total_count}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedNodeSlug(null)}
                    className="rounded-xl p-2 text-gray-400 transition hover:bg-white/5 hover:text-white"
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
                            <label className="mb-3 flex items-center gap-3 text-lg font-semibold text-white">
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
                                onClick={() => setExpandedTemplates((prev) => ({ ...prev, [group.key]: !expanded }))}
                                className="flex w-full items-center justify-between px-4 py-4 text-left"
                              >
                                <div className="font-semibold text-white">{group.title}</div>
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
            </>
          )}
        </div>
      </div>
    </PageShell>
  )
}

function getNodeAnchor(
  node: RoadmapNodeSummary,
  side: EdgeSide,
  offset: number,
  canvasBounds: { minX: number; minY: number },
) {
  const left = node.x - canvasBounds.minX + CANVAS_PADDING
  const top = node.y - canvasBounds.minY + CANVAS_PADDING

  if (side === 'top') {
    return { x: left + node.width * offset, y: top }
  }
  if (side === 'bottom') {
    return { x: left + node.width * offset, y: top + node.height }
  }
  if (side === 'left') {
    return { x: left, y: top + node.height * offset }
  }
  return { x: left + node.width, y: top + node.height * offset }
}

function buildEdgePath(
  source: { x: number; y: number },
  target: { x: number; y: number },
  sourceSide: EdgeSide,
  targetSide: EdgeSide,
) {
  if (sourceSide === 'right' && targetSide === 'left') {
    const dx = Math.max(70, Math.abs(target.x - source.x) * 0.35)
    return `M ${source.x} ${source.y} C ${source.x + dx} ${source.y}, ${target.x - dx} ${target.y}, ${target.x} ${target.y}`
  }

  if (sourceSide === 'left' && targetSide === 'right') {
    const dx = Math.max(70, Math.abs(target.x - source.x) * 0.35)
    return `M ${source.x} ${source.y} C ${source.x - dx} ${source.y}, ${target.x + dx} ${target.y}, ${target.x} ${target.y}`
  }

  if (sourceSide === 'bottom' && targetSide === 'top') {
    const dy = Math.max(70, Math.abs(target.y - source.y) * 0.5)
    return `M ${source.x} ${source.y} C ${source.x} ${source.y + dy}, ${target.x} ${target.y - dy}, ${target.x} ${target.y}`
  }

  if (sourceSide === 'top' && targetSide === 'bottom') {
    const dy = Math.max(70, Math.abs(target.y - source.y) * 0.5)
    return `M ${source.x} ${source.y} C ${source.x} ${source.y - dy}, ${target.x} ${target.y + dy}, ${target.x} ${target.y}`
  }

  const midY = (source.y + target.y) / 2
  return `M ${source.x} ${source.y} C ${source.x} ${midY}, ${target.x} ${midY}, ${target.x} ${target.y}`
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function progressPercent(node: Pick<RoadmapNodeSummary, 'completed_count' | 'total_count'>) {
  if (node.total_count === 0) return 0
  return (node.completed_count / node.total_count) * 100
}

function difficultyColor(difficulty: 'easy' | 'med' | 'hard') {
  if (difficulty === 'easy') return 'bg-[#3fc54d]'
  if (difficulty === 'med') return 'bg-[#eba81b]'
  return 'bg-[#ef3537]'
}

function difficultyHex(difficulty: 'easy' | 'med' | 'hard') {
  if (difficulty === 'easy') return '#3fc54d'
  if (difficulty === 'med') return '#eba81b'
  return '#ef3537'
}

function parseTags(input: string) {
  return input
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}

function PageShell({ children }: { children: ReactNode }) {
  return <div className="min-h-screen bg-[#191a1f] text-white">{children}</div>
}

function CenteredMessage({ text }: { text: string }) {
  return <div className="flex min-h-screen items-center justify-center text-gray-300">{text}</div>
}

function ErrorMessage({ message }: { message: string }) {
  return <div className="flex min-h-screen items-center justify-center text-red-300">{message}</div>
}

function RoadmapOverviewCard({
  roadmap,
  onZoomIn,
  onZoomOut,
  onFit,
}: {
  roadmap: RoadmapOverview
  onZoomIn: () => void
  onZoomOut: () => void
  onFit: () => void
}) {
  const totalLegend = roadmap.legend_counts.easy + roadmap.legend_counts.med + roadmap.legend_counts.hard
  const easyDeg = totalLegend === 0 ? 0 : (roadmap.legend_counts.easy / totalLegend) * 360
  const medDeg = totalLegend === 0 ? 0 : (roadmap.legend_counts.med / totalLegend) * 360
  const hardDeg = totalLegend === 0 ? 0 : (roadmap.legend_counts.hard / totalLegend) * 360
  const ringStyle = {
    background: `conic-gradient(#2e6d45 0deg ${easyDeg}deg, #7e6221 ${easyDeg}deg ${easyDeg + medDeg}deg, #67272f ${easyDeg + medDeg}deg ${easyDeg + medDeg + hardDeg}deg, rgba(255,255,255,0.08) ${easyDeg + medDeg + hardDeg}deg 360deg)`,
  }

  return (
    <div className="rounded-[26px] border border-white/8 bg-[#1d1f25]/96 p-5 shadow-[0_24px_76px_rgba(0,0,0,0.31)] backdrop-blur">
      <div className="mb-5 flex items-center gap-2 text-[14px] text-[#f0a14d]">
        <Flame size={15} />
        <span>Covers LeetCode Hot 100</span>
      </div>

      <div className="mb-5 flex items-center justify-between gap-4">
        <div className="space-y-3 text-[16px] text-[#d8d9dd]">
          <LegendRow color="bg-[#21c354]" label="Easy" />
          <LegendRow color="bg-[#ffc31a]" label="Med" />
          <LegendRow color="bg-[#f13233]" label="Hard" />
        </div>

        <div className="relative grid h-[108px] w-[108px] place-items-center rounded-full" style={ringStyle}>
          <div className="grid h-[78px] w-[78px] place-items-center rounded-full bg-[#1a1c22] text-center">
            <div>
              <div className="text-[20px] font-bold leading-none text-white">{roadmap.completed_problem_count}</div>
              <div className="mt-1 text-[12px] text-[#9b9da4]">/{roadmap.total_problem_goal}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-white/8 pt-4">
        <div className="grid grid-cols-3 gap-2 rounded-[18px] bg-[#17191f] p-3">
          <ControlButton ariaLabel="Zoom in" onClick={onZoomIn}>
            <SearchControlIcon mode="plus" />
          </ControlButton>
          <ControlButton ariaLabel="Zoom out" onClick={onZoomOut}>
            <SearchControlIcon mode="minus" />
          </ControlButton>
          <ControlButton ariaLabel="Fit roadmap" onClick={onFit}>
            <Maximize2 size={18} />
          </ControlButton>
        </div>
      </div>
    </div>
  )
}

function ControlButton({
  children,
  ariaLabel,
  onClick,
}: {
  children: ReactNode
  ariaLabel: string
  onClick: () => void
}) {
  return (
    <button
      aria-label={ariaLabel}
      onClick={onClick}
      className="flex h-12 items-center justify-center rounded-[16px] border border-white/8 bg-[#1f2127] text-[#d1d3d9] transition hover:border-white/15 hover:bg-[#252830] hover:text-white"
    >
      {children}
    </button>
  )
}

function LegendRow({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className={`h-4 w-4 rounded-full ${color}`} />
      <span>{label}</span>
    </div>
  )
}

function SearchControlIcon({ mode }: { mode: 'plus' | 'minus' }) {
  return (
    <span className="relative inline-flex h-5 w-5 items-center justify-center">
      <Search size={18} />
      <span className="absolute right-[-2px] top-[10px] h-2.5 w-2.5 rounded-full bg-[#1f2127]" />
      <span className="absolute right-[-1px] top-[11px] h-[1.5px] w-2.5 rounded-full bg-current" />
      {mode === 'plus' ? <span className="absolute right-[3px] top-[8px] h-2.5 w-[1.5px] rounded-full bg-current" /> : null}
    </span>
  )
}

function GroupNodeCard({
  node,
  childrenSlugs,
  topicNodeMap,
  selectedNodeSlug,
  onSelect,
  canvasBounds,
}: {
  node: RoadmapNodeSummary
  childrenSlugs: string[]
  topicNodeMap: Map<string, RoadmapNodeSummary>
  selectedNodeSlug: string | null
  onSelect: (slug: string) => void
  canvasBounds: { minX: number; minY: number }
}) {
  return (
    <div
      className="absolute rounded-[22px] border border-white/10 bg-[#1f2127]/92 shadow-[0_18px_52px_rgba(0,0,0,0.22)]"
      style={{
        left: node.x - canvasBounds.minX + CANVAS_PADDING,
        top: node.y - canvasBounds.minY + CANVAS_PADDING,
        width: node.width,
        height: node.height,
      }}
    >
      <div className="absolute left-4 right-4 top-3">
        <div className="text-[14px] font-semibold text-[#d9dbe1]">{node.title}</div>
        <div className="mt-3 h-[4px] rounded-full bg-white/9" />
      </div>

      {childrenSlugs.map((childSlug) => {
        const child = topicNodeMap.get(childSlug)
        if (!child) return null
        return (
          <div
            key={child.slug}
            className="absolute"
            style={{
              left: child.x - node.x,
              top: child.y - node.y,
            }}
          >
            <EmbeddedNodeCard
              node={child}
              selected={selectedNodeSlug === child.slug}
              onClick={() => onSelect(child.slug)}
            />
          </div>
        )
      })}
    </div>
  )
}

function EmbeddedNodeCard({
  node,
  selected,
  onClick,
}: {
  node: RoadmapNodeSummary
  selected: boolean
  onClick: () => void
}) {
  const ratio = progressPercent(node)
  return (
    <button
      onClick={onClick}
      className={`relative rounded-[14px] border px-4 pb-3 pt-3 text-left transition ${selected ? 'border-[#2e63d7] shadow-[0_0_0_1px_rgba(46,99,215,0.38)]' : 'border-white/10 hover:border-white/20'}`}
      style={{ backgroundColor: '#25272d', width: node.width, minHeight: node.height }}
    >
      <div className={`pr-4 text-[16px] font-semibold leading-tight ${selected ? 'text-[#4790ff]' : 'text-[#dfe2e7]'}`}>
        {node.title}
      </div>
      <span
        className="absolute right-3 top-3 h-3.5 w-3.5 rounded-full"
        style={{ backgroundColor: difficultyHex(node.difficulty) }}
      />
      <div className="mt-5 h-[4px] rounded-full bg-white/10">
        <div className="h-[4px] rounded-full bg-white/35" style={{ width: `${ratio}%` }} />
      </div>
    </button>
  )
}

function RoadmapNodeCard({
  node,
  selected,
  onClick,
  canvasBounds,
  largeTitle = false,
}: {
  node: RoadmapNodeSummary
  selected: boolean
  onClick: () => void
  canvasBounds: { minX: number; minY: number }
  largeTitle?: boolean
}) {
  const ratio = progressPercent(node)
  return (
    <button
      onClick={onClick}
      className={`absolute rounded-[18px] border px-5 pb-3 pt-3 text-left shadow-[0_14px_44px_rgba(0,0,0,0.2)] transition ${selected ? 'border-[#2e63d7] shadow-[0_0_0_1px_rgba(46,99,215,0.4)]' : 'border-white/10 hover:border-white/20'}`}
      style={{
        left: node.x - canvasBounds.minX + CANVAS_PADDING,
        top: node.y - canvasBounds.minY + CANVAS_PADDING,
        width: node.width,
        minHeight: node.height,
        backgroundColor: '#26282e',
      }}
    >
      <div className={`pr-5 text-center font-semibold leading-tight ${selected ? 'text-[#4790ff]' : 'text-[#e1e4ea]'} ${largeTitle ? 'text-[22px]' : 'text-[17px]'}`}>
        {node.title}
      </div>
      <span
        className="absolute right-4 top-4 h-3.5 w-3.5 rounded-full"
        style={{ backgroundColor: difficultyHex(node.difficulty) }}
      />
      <div className="mt-4 h-[4px] rounded-full bg-white/10">
        <div className="h-[4px] rounded-full bg-white/35" style={{ width: `${ratio}%` }} />
      </div>
    </button>
  )
}

function PanelSection({
  title,
  icon,
  children,
}: {
  title: string
  icon: ReactNode
  children: ReactNode
}) {
  return (
    <section>
      <div className="mb-4 flex items-center gap-3 text-2xl font-bold text-white">
        <span className="text-cyan-300">{icon}</span>
        <h3>{title}</h3>
      </div>
      {children}
    </section>
  )
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-5 text-gray-400">{text}</div>
}

function MarkdownBlock({ content }: { content: string }) {
  return (
    <div className="prose prose-invert max-w-none prose-pre:bg-[#101216] prose-pre:text-gray-100 prose-code:text-cyan-200">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}
