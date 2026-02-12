import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
    Briefcase, Search, Filter, Plus, MapPin,
    ChevronRight, Calendar, BarChart2, MoreHorizontal
} from 'lucide-react';
import { projectsApi } from '../services/api';
import { queryKeys } from '../lib/queryClient';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "../components/ui/table";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { SkeletonTable, SkeletonText } from '../components/SkeletonScreen';
import { FadeIn } from '../components/PageTransition';

export const Projects = () => {
    const navigate = useNavigate();
    const [search, setSearch] = useState('');

    const { data: projects = [], isLoading, isError, error, refetch } = useQuery({
        queryKey: queryKeys.projects.list(100),
        queryFn: () => projectsApi.list(100).then(res => res.data),
        staleTime: 5 * 60 * 1000,
    });

    const filteredProjects = useMemo(() => 
        projects.filter((p: any) =>
            (p.name?.toLowerCase().includes(search.toLowerCase())) ||
            (p.address?.toLowerCase().includes(search.toLowerCase()))
        ),
        [projects, search]
    );

    const activeProjects = useMemo(() => 
        projects.filter((p: any) => p.status === 'active').length,
        [projects]
    );

    // Show skeleton on first load
    if (isLoading && projects.length === 0) {
        return (
            <div className="space-y-8 p-8">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div>
                        <SkeletonText className="w-56" lineHeight="h-8" />
                        <div className="mt-2">
                            <SkeletonText className="w-80" lines={1} />
                        </div>
                    </div>
                    <div className="h-10 w-32 bg-gray-100 rounded-xl animate-pulse" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                            <SkeletonText className="w-32" />
                            <SkeletonText className="w-16 mt-2" lineHeight="h-8" />
                        </div>
                    ))}
                </div>
                <SkeletonTable rows={5} columns={5} />
            </div>
        );
    }

    // Error state
    if (isError) {
        return (
            <div className="space-y-8 p-8">
                <FadeIn>
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-12 text-center">
                        <p className="text-red-600 mb-4">
                            {error instanceof Error ? error.message : 'Unable to load projects. Check that the backend is running.'}
                        </p>
                        <Button onClick={() => refetch()} className="bg-orange-600 hover:bg-orange-700 text-white">
                            Retry
                        </Button>
                    </div>
                </FadeIn>
            </div>
        );
    }

    return (
        <div className="space-y-8 p-8">
            {/* Header */}
            <FadeIn>
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 tracking-tight font-display">Industrial Projects</h1>
                        <p className="text-gray-500 mt-2 text-lg">Group quotes by site address and construction project.</p>
                    </div>
                    <div className="flex gap-3">
                        <Button
                            variant="outline"
                            onClick={() => {/* TODO: Analytics */ }}
                            className="rounded-xl border-gray-200"
                        >
                            <BarChart2 className="mr-2 h-4 w-4" /> Sales Reporting
                        </Button>
                        <Button
                            onClick={() => {/* TODO: Create Project Modal */ }}
                            className="bg-orange-600 hover:bg-orange-700 text-white shadow-lg hover:shadow-orange-500/20 transition-all rounded-xl px-6"
                        >
                            <Plus className="mr-2 h-4 w-4" /> New Project
                        </Button>
                    </div>
                </div>
            </FadeIn>

            {/* Stats Overview */}
            <FadeIn delay={0.05}>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                        <div className="text-sm font-medium text-gray-500 mb-1">Active Projects</div>
                        <div className="text-3xl font-bold text-gray-900">{activeProjects}</div>
                    </div>
                    <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                        <div className="text-sm font-medium text-gray-500 mb-1">Avg. Quotes per Project</div>
                        <div className="text-3xl font-bold text-gray-900">3.4</div>
                    </div>
                    <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                        <div className="text-sm font-medium text-gray-500 mb-1">Total Project Pipeline</div>
                        <div className="text-3xl font-bold text-orange-600">$1.2M</div>
                    </div>
                </div>
            </FadeIn>

            {/* Content Card */}
            <FadeIn delay={0.1}>
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                    {/* Toolbar */}
                    <div className="p-6 border-b border-gray-100 flex flex-col md:flex-row gap-4 justify-between items-center">
                        <div className="relative w-full md:w-96">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
                            <input
                                type="text"
                                placeholder="Search projects or addresses..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full pl-10 pr-4 py-2.5 bg-gray-50/50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all"
                            />
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" className="text-gray-600 border-gray-200 rounded-xl">
                                <Filter className="mr-2 h-4 w-4" /> Filter
                            </Button>
                        </div>
                    </div>

                    {/* Table */}
                    <div className="relative">
                        {filteredProjects.length === 0 ? (
                            <div className="p-16 text-center">
                                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Briefcase className="text-gray-300" size={24} />
                                </div>
                                <h3 className="text-lg font-medium text-gray-900">No projects found</h3>
                                <p className="text-gray-500 mt-1">
                                    {search ? `No results for "${search}"` : 'Industrial trade thrives on project grouping. Create your first project site.'}
                                </p>
                                {!search && (
                                    <Button
                                        onClick={() => {/* TODO: Create Project Modal */ }}
                                        className="mt-6 bg-orange-600 hover:bg-orange-700 text-white rounded-xl"
                                    >
                                        <Plus className="mr-2 h-4 w-4" /> Create Project
                                    </Button>
                                )}
                            </div>
                        ) : (
                            <Table>
                                <TableHeader className="bg-gray-50/50">
                                    <TableRow>
                                        <TableHead className="pl-6 py-4 text-xs uppercase tracking-wider font-semibold text-gray-500">Project Name & ID</TableHead>
                                        <TableHead className="py-4 text-xs uppercase tracking-wider font-semibold text-gray-500">Project Address</TableHead>
                                        <TableHead className="py-4 text-xs uppercase tracking-wider font-semibold text-gray-500">Status</TableHead>
                                        <TableHead className="py-4 text-xs uppercase tracking-wider font-semibold text-gray-500">Created</TableHead>
                                        <TableHead className="text-right pr-6 py-4 text-xs uppercase tracking-wider font-semibold text-gray-500">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredProjects.map((project: any) => (
                                        <TableRow
                                            key={project.id}
                                            className="group hover:bg-gray-50/50 transition-colors cursor-pointer border-b border-gray-100 last:border-0"
                                            onClick={() => navigate(`/projects/${project.id}`)}
                                        >
                                            <TableCell className="pl-6 py-4">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center text-orange-700">
                                                        <Briefcase size={18} />
                                                    </div>
                                                    <div>
                                                        <div className="font-semibold text-gray-900">{project.name}</div>
                                                        <div className="text-xs text-gray-500 font-mono mt-0.5">#{project.id?.slice(0, 8)}</div>
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                                    <MapPin size={14} className="text-gray-400 shrink-0" />
                                                    <span className="truncate max-w-[200px]">{project.address || 'No address provided'}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="secondary" className="bg-green-100 text-green-700 hover:bg-green-100 border-none rounded-full px-3 py-0.5 text-[10px] uppercase font-bold tracking-wider">
                                                    {project.status || 'Active'}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                                    <Calendar size={14} className="text-gray-400" />
                                                    {new Date(project.created_at).toLocaleDateString()}
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-right pr-6">
                                                <div className="flex items-center justify-end gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="text-gray-400 hover:text-gray-600 rounded-lg w-8 h-8"
                                                    >
                                                        <MoreHorizontal size={18} />
                                                    </Button>
                                                    <ChevronRight className="text-gray-300 group-hover:text-orange-500 transition-colors" size={18} />
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </div>
                </div>
            </FadeIn>
        </div>
    );
};

export default Projects;
