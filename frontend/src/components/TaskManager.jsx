import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TaskCard from './TaskCard';
import CreateTaskModal from './CreateTaskModal';

const TaskManager = ({
  tasks,
  loading,
  onTaskUpdate,
  onCreateTask,
  onRefresh,
}) => {
  const [selectedTask, setSelectedTask] = useState(null);
  const [filterBy, setFilterBy] = useState('all'); // all, urgent, high, medium, low
  const [sortBy, setSortBy] = useState('priority'); // priority, risk, created
  const [showCreateModal, setShowCreateModal] = useState(false);

  const getFilteredAndSortedTasks = () => {
    if (!tasks) return [];

    let filtered = [...tasks];

    // Apply filters
    if (filterBy !== 'all') {
      filtered = filtered.filter(task => {
        if (filterBy === 'urgent') return task.priority === 'urgent';
        if (filterBy === 'high')
          return task.priority === 'high' || task.risk_level === 'high';
        if (filterBy === 'medium')
          return task.priority === 'medium' || task.risk_level === 'medium';
        if (filterBy === 'low')
          return task.priority === 'low' || task.risk_level === 'low';
        return true;
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === 'priority') {
        const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      }
      if (sortBy === 'risk') {
        const riskOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        return riskOrder[b.risk_level] - riskOrder[a.risk_level];
      }
      if (sortBy === 'created') {
        return (
          new Date(b.created_at || Date.now()) -
          new Date(a.created_at || Date.now())
        );
      }
      return 0;
    });

    return filtered;
  };

  const filteredTasks = getFilteredAndSortedTasks();

  const getTaskStats = () => {
    if (!tasks) return { total: 0, urgent: 0, high_risk: 0, completed: 0 };

    return {
      total: tasks.length,
      urgent: tasks.filter(t => t.priority === 'urgent').length,
      high_risk: tasks.filter(
        t => t.risk_level === 'high' || t.risk_level === 'critical'
      ).length,
      completed: tasks.filter(t => t.status === 'completed').length,
    };
  };

  const stats = getTaskStats();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-16 h-16 border-4 border-luxury-gold border-t-rose-gold rounded-full animate-spin mb-4 mx-auto"></div>
          <p className="text-gray-600 font-elegant">
            Organizing your luxury task atelier...
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        className="text-center"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="text-4xl font-fashion font-bold bg-gradient-to-r from-luxury-gold via-rose-gold to-elegant-silver bg-clip-text text-transparent mb-4">
          Task Atelier
        </h2>
        <p className="text-gray-600 text-lg font-elegant max-w-2xl mx-auto">
          Your curated collection of high-priority tasks, expertly organized by
          risk and impact to ensure your luxury brand maintains its excellence.
        </p>
      </motion.div>

      {/* Stats Overview */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-4 gap-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        {[
          {
            label: 'Total Tasks',
            value: stats.total,
            color: 'bg-rose-gold',
            icon: '📋',
          },
          {
            label: 'Urgent',
            value: stats.urgent,
            color: 'bg-red-500',
            icon: '🚨',
          },
          {
            label: 'High Risk',
            value: stats.high_risk,
            color: 'bg-orange-500',
            icon: '⚠️',
          },
          {
            label: 'Completed',
            value: stats.completed,
            color: 'bg-green-500',
            icon: '✅',
          },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            className="fashion-card text-center"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
          >
            <div
              className={`w-12 h-12 ${stat.color} rounded-full flex items-center justify-center text-white text-xl mx-auto mb-3 shadow-elegant`}
            >
              {stat.icon}
            </div>
            <div className="text-3xl font-bold text-gray-800 mb-1">
              {stat.value}
            </div>
            <div className="text-sm text-gray-600">{stat.label}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Controls */}
      <motion.div
        className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0 sm:space-x-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          {[
            { id: 'all', label: 'All Tasks', icon: '📋' },
            { id: 'urgent', label: 'Urgent', icon: '🚨' },
            { id: 'high', label: 'High Priority', icon: '⚠️' },
            { id: 'medium', label: 'Medium', icon: '📊' },
            { id: 'low', label: 'Low', icon: '📝' },
          ].map(filter => (
            <button
              key={filter.id}
              className={`px-4 py-2 rounded-full font-medium transition-all duration-300 ${
                filterBy === filter.id
                  ? 'bg-luxury-gradient text-white shadow-elegant'
                  : 'bg-white/80 text-gray-700 hover:bg-rose-gold/20'
              }`}
              onClick={() => setFilterBy(filter.id)}
            >
              <span className="mr-1">{filter.icon}</span>
              {filter.label}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="flex space-x-3">
          {/* Sort Dropdown */}
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="px-4 py-2 bg-white/90 border border-rose-gold/30 rounded-lg font-medium text-gray-700 focus:ring-2 focus:ring-luxury-gold focus:border-luxury-gold transition-all duration-300"
          >
            <option value="priority">Sort by Priority</option>
            <option value="risk">Sort by Risk</option>
            <option value="created">Sort by Created</option>
          </select>

          <button
            className="luxury-button"
            onClick={() => setShowCreateModal(true)}
          >
            <span className="mr-2">✨</span>
            Create Task
          </button>

          <button
            className="px-4 py-2 bg-white/90 border border-rose-gold/30 rounded-lg font-medium text-gray-700 hover:bg-rose-gold/20 transition-all duration-300"
            onClick={onRefresh}
          >
            🔄
          </button>
        </div>
      </motion.div>

      {/* Tasks Grid */}
      <AnimatePresence>
        {filteredTasks.length > 0 ? (
          <motion.div
            className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6"
            initial="hidden"
            animate="visible"
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: {
                  staggerChildren: 0.1,
                },
              },
            }}
          >
            {filteredTasks.map((task, _index) => (
              <motion.div
                key={task.id}
                variants={{
                  hidden: { opacity: 0, y: 30, scale: 0.9 },
                  visible: {
                    opacity: 1,
                    y: 0,
                    scale: 1,
                    transition: {
                      duration: 0.4,
                      ease: 'easeOut',
                    },
                  },
                }}
              >
                <TaskCard
                  task={task}
                  onUpdate={updates => onTaskUpdate(task.id, updates)}
                  onClick={() => setSelectedTask(task)}
                />
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div
            className="text-center py-16"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="text-6xl mb-4">✨</div>
            <h3 className="text-xl font-fashion font-semibold text-gray-700 mb-2">
              No Tasks Found
            </h3>
            <p className="text-gray-500 mb-6">
              Your atelier is pristine! Create a new task or adjust your
              filters.
            </p>
            <button
              className="luxury-button"
              onClick={() => setShowCreateModal(true)}
            >
              <span className="mr-2">✨</span>
              Create Your First Task
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Task Modal */}
      <CreateTaskModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={onCreateTask}
      />

      {/* Task Details Modal */}
      {selectedTask && (
        <motion.div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setSelectedTask(null)}
        >
          <motion.div
            className="bg-white rounded-3xl p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-luxury"
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            onClick={e => e.stopPropagation()}
          >
            <TaskCard
              task={selectedTask}
              onUpdate={updates => onTaskUpdate(selectedTask.id, updates)}
              isExpanded={true}
              showDetails={true}
            />
          </motion.div>
        </motion.div>
      )}
    </div>
  );
};

export default TaskManager;
