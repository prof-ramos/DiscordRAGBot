// ============================================================================
// Discord RAG Bot - TypeScript Type Definitions
// ============================================================================
// Auto-generated from Supabase schema
// Date: 2025-11-05
//
// These types provide type-safety for the database schema
// Use with Supabase client for full TypeScript support
// ============================================================================

export interface Database {
  public: {
    Tables: {
      documents: {
        Row: {
          id: number;
          content: string;
          embedding: number[]; // vector(1536)
          metadata: Record<string, any>;
          document_id: string; // UUID
          chunk_index: number;
          source_type: string;
          source_name: string | null;
          created_at: string; // timestamptz
          updated_at: string; // timestamptz
        };
        Insert: {
          id?: never; // auto-generated
          content: string;
          embedding: number[];
          metadata?: Record<string, any>;
          document_id?: string;
          chunk_index?: number;
          source_type?: string;
          source_name?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          content?: string;
          embedding?: number[];
          metadata?: Record<string, any>;
          chunk_index?: number;
          source_type?: string;
          source_name?: string | null;
          updated_at?: string;
        };
      };

      server_configs: {
        Row: {
          guild_id: string;
          filter_level: 'conservador' | 'moderado' | 'liberal';
          settings: Record<string, any>;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          guild_id: string;
          filter_level?: 'conservador' | 'moderado' | 'liberal';
          settings?: Record<string, any>;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          filter_level?: 'conservador' | 'moderado' | 'liberal';
          settings?: Record<string, any>;
          updated_at?: string;
        };
      };

      query_history: {
        Row: {
          id: number;
          user_id: string;
          guild_id: string | null;
          question: string;
          answer: string;
          query_type: string;
          sources_count: number;
          response_time_ms: number | null;
          tokens_used: number | null;
          model_used: string | null;
          filter_level_used: string | null;
          metadata: Record<string, any>;
          created_at: string;
        };
        Insert: {
          id?: never;
          user_id: string;
          guild_id?: string | null;
          question: string;
          answer: string;
          query_type?: string;
          sources_count?: number;
          response_time_ms?: number | null;
          tokens_used?: number | null;
          model_used?: string | null;
          filter_level_used?: string | null;
          metadata?: Record<string, any>;
          created_at?: string;
        };
        Update: {
          // Query history is generally immutable
          metadata?: Record<string, any>;
        };
      };

      query_cache: {
        Row: {
          cache_key: string;
          question: string;
          answer: string;
          sources: Array<any>;
          hit_count: number;
          metadata: Record<string, any>;
          created_at: string;
          expires_at: string;
        };
        Insert: {
          cache_key: string;
          question: string;
          answer: string;
          sources?: Array<any>;
          hit_count?: number;
          metadata?: Record<string, any>;
          created_at?: string;
          expires_at: string;
        };
        Update: {
          answer?: string;
          sources?: Array<any>;
          hit_count?: number;
          metadata?: Record<string, any>;
          expires_at?: string;
        };
      };

      rate_limits: {
        Row: {
          user_id: string;
          request_count: number;
          window_start: string;
          window_duration: number;
          last_request_at: string;
          total_requests_all_time: number;
        };
        Insert: {
          user_id: string;
          request_count?: number;
          window_start?: string;
          window_duration?: number;
          last_request_at?: string;
          total_requests_all_time?: number;
        };
        Update: {
          request_count?: number;
          window_start?: string;
          window_duration?: number;
          last_request_at?: string;
          total_requests_all_time?: number;
        };
      };

      user_profiles: {
        Row: {
          user_id: string;
          total_queries: number;
          total_feedback_given: number;
          preferred_filter_level: string | null;
          preferred_query_type: string | null;
          first_seen: string;
          last_seen: string;
          metadata: Record<string, any>;
        };
        Insert: {
          user_id: string;
          total_queries?: number;
          total_feedback_given?: number;
          preferred_filter_level?: string | null;
          preferred_query_type?: string | null;
          first_seen?: string;
          last_seen?: string;
          metadata?: Record<string, any>;
        };
        Update: {
          total_queries?: number;
          total_feedback_given?: number;
          preferred_filter_level?: string | null;
          preferred_query_type?: string | null;
          last_seen?: string;
          metadata?: Record<string, any>;
        };
      };

      feedback: {
        Row: {
          id: number;
          query_history_id: number | null;
          user_id: string;
          rating: number | null; // 1-5
          comment: string | null;
          feedback_type: string;
          created_at: string;
        };
        Insert: {
          id?: never;
          query_history_id?: number | null;
          user_id: string;
          rating?: number | null;
          comment?: string | null;
          feedback_type?: string;
          created_at?: string;
        };
        Update: {
          comment?: string | null;
          rating?: number | null;
        };
      };

      audit_logs: {
        Row: {
          id: number;
          table_name: string;
          operation: 'INSERT' | 'UPDATE' | 'DELETE' | 'SELECT';
          user_id: string | null;
          record_id: string | null;
          old_data: Record<string, any> | null;
          new_data: Record<string, any> | null;
          ip_address: string | null;
          user_agent: string | null;
          metadata: Record<string, any>;
          created_at: string;
        };
        Insert: {
          id?: never;
          table_name: string;
          operation: 'INSERT' | 'UPDATE' | 'DELETE' | 'SELECT';
          user_id?: string | null;
          record_id?: string | null;
          old_data?: Record<string, any> | null;
          new_data?: Record<string, any> | null;
          ip_address?: string | null;
          user_agent?: string | null;
          metadata?: Record<string, any>;
          created_at?: string;
        };
        Update: {
          // Audit logs are immutable
        };
      };
    };

    Functions: {
      match_documents: {
        Args: {
          query_embedding: number[];
          match_count?: number;
          filter?: Record<string, any>;
        };
        Returns: Array<{
          id: number;
          content: string;
          metadata: Record<string, any>;
          document_id: string;
          source_name: string | null;
          similarity: number;
        }>;
      };

      clean_expired_cache: {
        Args: Record<string, never>;
        Returns: number;
      };

      reset_rate_limit_if_expired: {
        Args: {
          p_user_id: string;
        };
        Returns: boolean;
      };

      update_user_profile: {
        Args: {
          p_user_id: string;
          p_query_type?: string | null;
        };
        Returns: void;
      };

      set_user_context: {
        Args: {
          p_user_id: string;
        };
        Returns: void;
      };

      set_guild_context: {
        Args: {
          p_guild_id: string;
        };
        Returns: void;
      };

      clear_context: {
        Args: Record<string, never>;
        Returns: void;
      };
    };
  };
}

// ============================================================================
// Convenience Types
// ============================================================================

export type Document = Database['public']['Tables']['documents']['Row'];
export type DocumentInsert = Database['public']['Tables']['documents']['Insert'];
export type DocumentUpdate = Database['public']['Tables']['documents']['Update'];

export type ServerConfig = Database['public']['Tables']['server_configs']['Row'];
export type ServerConfigInsert = Database['public']['Tables']['server_configs']['Insert'];
export type ServerConfigUpdate = Database['public']['Tables']['server_configs']['Update'];

export type QueryHistory = Database['public']['Tables']['query_history']['Row'];
export type QueryHistoryInsert = Database['public']['Tables']['query_history']['Insert'];

export type QueryCache = Database['public']['Tables']['query_cache']['Row'];
export type QueryCacheInsert = Database['public']['Tables']['query_cache']['Insert'];
export type QueryCacheUpdate = Database['public']['Tables']['query_cache']['Update'];

export type RateLimit = Database['public']['Tables']['rate_limits']['Row'];
export type RateLimitInsert = Database['public']['Tables']['rate_limits']['Insert'];
export type RateLimitUpdate = Database['public']['Tables']['rate_limits']['Update'];

export type UserProfile = Database['public']['Tables']['user_profiles']['Row'];
export type UserProfileInsert = Database['public']['Tables']['user_profiles']['Insert'];
export type UserProfileUpdate = Database['public']['Tables']['user_profiles']['Update'];

export type Feedback = Database['public']['Tables']['feedback']['Row'];
export type FeedbackInsert = Database['public']['Tables']['feedback']['Insert'];

export type AuditLog = Database['public']['Tables']['audit_logs']['Row'];
export type AuditLogInsert = Database['public']['Tables']['audit_logs']['Insert'];

export type FilterLevel = 'conservador' | 'moderado' | 'liberal';
export type QueryType = 'RAG' | 'DM' | 'Mention' | 'Slash';
export type FeedbackType = 'rating' | 'report' | 'suggestion';
export type Operation = 'INSERT' | 'UPDATE' | 'DELETE' | 'SELECT';

// ============================================================================
// Helper Types
// ============================================================================

export interface MatchDocumentsResult {
  id: number;
  content: string;
  metadata: Record<string, any>;
  document_id: string;
  source_name: string | null;
  similarity: number;
}

export interface QueryStats {
  total_queries: number;
  avg_response_time: number;
  total_sources_used: number;
  most_common_query_type: QueryType;
}

export interface UserStats {
  user_id: string;
  total_queries: number;
  total_feedback: number;
  first_seen: string;
  last_seen: string;
  preferred_filter: FilterLevel | null;
}
