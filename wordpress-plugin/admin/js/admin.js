/**
 * Skyy Rose AI Agents - Admin JavaScript
 * 
 * @package SkyyRoseAIAgents
 * @since 1.0.0
 */

(function($) {
    'use strict';

    // Main Dashboard object
    window.SkyyRoseDashboard = {
        
        /**
         * Initialize dashboard
         */
        init: function() {
            this.bindEvents();
            this.initializeTabs();
            this.setupAjax();
            this.startAutoRefresh();
        },

        /**
         * Bind event listeners
         */
        bindEvents: function() {
            // Agent action buttons
            $(document).on('click', '.run-agent', this.runAgentAction);
            $(document).on('click', '.agent-action', this.runAgentAction);
            $(document).on('click', '.action-button', this.runAgentAction);
            $(document).on('click', '.run-performance-check', this.runAgentAction);
            $(document).on('click', '.run-security-scan', this.runAgentAction);
            
            // Bulk actions
            $(document).on('click', '.run-all-agents', this.runAllAgents);
            
            // Settings tabs
            $(document).on('click', '.nav-tab', this.switchTab);
            
            // Auto-refresh toggle
            $(document).on('change', '#auto-refresh', this.toggleAutoRefresh);
        },

        /**
         * Initialize settings tabs
         */
        initializeTabs: function() {
            // Show first tab by default
            $('.tab-content').hide();
            $('.tab-content:first').show();
            
            // Handle tab switching
            $('.nav-tab').click(function(e) {
                e.preventDefault();
                
                var target = $(this).attr('href');
                
                // Update tab states
                $('.nav-tab').removeClass('nav-tab-active');
                $(this).addClass('nav-tab-active');
                
                // Show target content
                $('.tab-content').hide();
                $(target).show();
            });
        },

        /**
         * Setup AJAX defaults
         */
        setupAjax: function() {
            $.ajaxSetup({
                beforeSend: function(xhr) {
                    xhr.setRequestHeader('X-WP-Nonce', skyyRoseAI.nonce);
                }
            });
        },

        /**
         * Run individual agent action
         */
        runAgentAction: function(e) {
            e.preventDefault();
            
            var $button = $(this);
            var agent = $button.data('agent');
            var action = $button.data('action');
            
            if (!agent || !action) {
                SkyyRoseDashboard.showNotification('error', skyyRoseAI.strings.error);
                return;
            }

            // Confirm action if it's potentially disruptive
            if (['optimize_wordpress', 'run_security_scan'].includes(action)) {
                if (!confirm(skyyRoseAI.strings.confirm_action)) {
                    return;
                }
            }

            SkyyRoseDashboard.executeAgentAction(agent, action, $button);
        },

        /**
         * Run all agents
         */
        runAllAgents: function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to run all agents? This may take several minutes.')) {
                return;
            }

            var $button = $(this);
            var agents = [
                { agent: 'brand_intelligence', action: 'analyze_brand' },
                { agent: 'inventory', action: 'scan_assets' },
                { agent: 'performance', action: 'check_performance' },
                { agent: 'security', action: 'run_security_scan' }
            ];

            $button.prop('disabled', true).text('Running All Agents...');

            // Run agents sequentially
            SkyyRoseDashboard.runAgentsSequentially(agents, 0, $button);
        },

        /**
         * Execute agent action via AJAX
         */
        executeAgentAction: function(agent, action, $button) {
            var originalText = $button.text();
            
            $button.prop('disabled', true)
                   .addClass('loading')
                   .text(skyyRoseAI.strings.loading);

            $.ajax({
                url: '/wp-json/skyy-rose-ai/v1/agents/' + agent + '/' + action,
                method: 'POST',
                data: {
                    nonce: skyyRoseAI.nonce
                },
                success: function(response) {
                    if (response.success) {
                        SkyyRoseDashboard.showNotification('success', response.message || skyyRoseAI.strings.success);
                        SkyyRoseDashboard.updateDashboardData();
                    } else {
                        SkyyRoseDashboard.showNotification('error', response.error || skyyRoseAI.strings.error);
                    }
                },
                error: function(xhr, status, error) {
                    var errorMessage = skyyRoseAI.strings.error;
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMessage = xhr.responseJSON.message;
                    }
                    SkyyRoseDashboard.showNotification('error', errorMessage);
                },
                complete: function() {
                    $button.prop('disabled', false)
                           .removeClass('loading')
                           .text(originalText);
                }
            });
        },

        /**
         * Run agents sequentially
         */
        runAgentsSequentially: function(agents, index, $button) {
            if (index >= agents.length) {
                $button.prop('disabled', false).text('Run All Agents');
                SkyyRoseDashboard.showNotification('success', 'All agents completed successfully!');
                SkyyRoseDashboard.updateDashboardData();
                return;
            }

            var currentAgent = agents[index];
            
            $.ajax({
                url: '/wp-json/skyy-rose-ai/v1/agents/' + currentAgent.agent + '/' + currentAgent.action,
                method: 'POST',
                data: {
                    nonce: skyyRoseAI.nonce
                },
                success: function(response) {
                    // Continue to next agent
                    setTimeout(function() {
                        SkyyRoseDashboard.runAgentsSequentially(agents, index + 1, $button);
                    }, 1000);
                },
                error: function() {
                    // Continue even if one fails
                    setTimeout(function() {
                        SkyyRoseDashboard.runAgentsSequentially(agents, index + 1, $button);
                    }, 1000);
                }
            });
        },

        /**
         * Update dashboard data
         */
        updateDashboardData: function() {
            $.ajax({
                url: '/wp-json/skyy-rose-ai/v1/dashboard',
                method: 'GET',
                success: function(response) {
                    // Update overview cards
                    SkyyRoseDashboard.updateOverviewCards(response.quick_stats);
                    
                    // Update recent activities
                    SkyyRoseDashboard.updateRecentActivities(response.recent_activities);
                    
                    // Update performance data
                    if (response.performance_overview) {
                        SkyyRoseDashboard.updatePerformanceWidget(response.performance_overview);
                    }
                    
                    // Update security data
                    if (response.security_overview) {
                        SkyyRoseDashboard.updateSecurityWidget(response.security_overview);
                    }
                }
            });
        },

        /**
         * Update overview cards
         */
        updateOverviewCards: function(stats) {
            if (stats.total_activities !== undefined) {
                $('.activities-card .card-value').text(stats.activities_today);
            }
            if (stats.enabled_agents !== undefined) {
                $('.agents-card .card-value').html(stats.enabled_agents + '<span class="unit">/5</span>');
            }
        },

        /**
         * Update recent activities list
         */
        updateRecentActivities: function(activities) {
            var $activitiesList = $('.activities-list');
            if (!$activitiesList.length || !activities) return;

            // Clear existing activities
            $activitiesList.empty();

            if (activities.length === 0) {
                $activitiesList.html('<div class="no-activities"><p>No recent activities.</p></div>');
                return;
            }

            // Add new activities
            activities.forEach(function(activity) {
                var activityHtml = SkyyRoseDashboard.buildActivityHtml(activity);
                $activitiesList.append(activityHtml);
            });
        },

        /**
         * Build activity HTML
         */
        buildActivityHtml: function(activity) {
            var icon = SkyyRoseDashboard.getAgentIcon(activity.agent_type);
            var agentName = SkyyRoseDashboard.getAgentDisplayName(activity.agent_type);
            var actionName = SkyyRoseDashboard.formatActionName(activity.action);
            var timeAgo = SkyyRoseDashboard.timeAgo(activity.created_at);
            
            return '<div class="activity-item status-' + activity.status + '">' +
                   '<div class="activity-icon">' + icon + '</div>' +
                   '<div class="activity-content">' +
                   '<div class="activity-title">' +
                   '<strong>' + agentName + '</strong> ' + actionName +
                   '</div>' +
                   '<div class="activity-meta">' +
                   '<span class="activity-status status-' + activity.status + '">' + 
                   activity.status.charAt(0).toUpperCase() + activity.status.slice(1) + '</span>' +
                   '<span class="activity-time">' + timeAgo + '</span>' +
                   '</div>' +
                   '</div>' +
                   '</div>';
        },

        /**
         * Update performance widget
         */
        updatePerformanceWidget: function(performance) {
            if (performance.score !== undefined) {
                $('.performance-card .card-value').html(performance.score + '<span class="unit">%</span>');
                
                // Update trend
                var $trend = $('.performance-card .card-trend');
                $trend.removeClass('up down').addClass(performance.trend);
            }
        },

        /**
         * Update security widget
         */
        updateSecurityWidget: function(security) {
            if (security.threat_level !== undefined) {
                var $securityStatus = $('.security-status');
                $securityStatus.removeClass('security-low security-medium security-high security-critical')
                              .addClass('security-' + security.threat_level);
                
                $('.security-level').text(security.threat_level.charAt(0).toUpperCase() + 
                                         security.threat_level.slice(1) + ' Risk');
            }
        },

        /**
         * Show notification
         */
        showNotification: function(type, message) {
            var noticeClass = 'notice notice-' + (type === 'error' ? 'error' : 'success');
            var $notice = $('<div class="' + noticeClass + ' is-dismissible skyy-rose-notice">' +
                           '<p>' + message + '</p>' +
                           '<button type="button" class="notice-dismiss">' +
                           '<span class="screen-reader-text">Dismiss this notice.</span>' +
                           '</button>' +
                           '</div>');
            
            $('.wrap h1').after($notice);
            
            // Auto-dismiss after 5 seconds
            setTimeout(function() {
                $notice.fadeOut();
            }, 5000);
            
            // Handle manual dismiss
            $notice.find('.notice-dismiss').click(function() {
                $notice.fadeOut();
            });
        },

        /**
         * Start auto-refresh
         */
        startAutoRefresh: function() {
            // Refresh dashboard data every 2 minutes
            setInterval(function() {
                SkyyRoseDashboard.updateDashboardData();
            }, 120000);
        },

        /**
         * Helper functions
         */
        getAgentIcon: function(agentType) {
            var icons = {
                'brand_intelligence': '🎨',
                'inventory': '📦',
                'wordpress': '🌐',
                'performance': '⚡',
                'security': '🛡️'
            };
            return icons[agentType] || '🤖';
        },

        getAgentDisplayName: function(agentType) {
            var names = {
                'brand_intelligence': 'Brand Intelligence',
                'inventory': 'Inventory',
                'wordpress': 'WordPress',
                'performance': 'Performance',
                'security': 'Security'
            };
            return names[agentType] || agentType.replace('_', ' ');
        },

        formatActionName: function(action) {
            return action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        },

        timeAgo: function(dateString) {
            var now = new Date();
            var past = new Date(dateString);
            var diffMs = now - past;
            var diffMins = Math.floor(diffMs / 60000);
            var diffHours = Math.floor(diffMins / 60);
            var diffDays = Math.floor(diffHours / 24);

            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return diffMins + ' min ago';
            if (diffHours < 24) return diffHours + ' hour' + (diffHours > 1 ? 's' : '') + ' ago';
            return diffDays + ' day' + (diffDays > 1 ? 's' : '') + ' ago';
        }
    };

    // Initialize when document is ready
    $(document).ready(function() {
        if (typeof skyyRoseAI !== 'undefined') {
            SkyyRoseDashboard.init();
        }
    });

})(jQuery);