/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Reader for the Python bridge's JSONL request log
 *
 * The worldserver never builds an LLM prompt itself, so the
 * only place a prompt and its response sit side by side is
 * the bridge's request log (tools/chatter_request_logger.py).
 * Both processes bind-mount the same host directory, so the
 * worldserver can tail that file and serve it to the Chatter
 * Log addon.
 */

#ifndef LLM_CHATTER_REQUEST_LOG_H
#define LLM_CHATTER_REQUEST_LOG_H

#include "Define.h"
#include <string>
#include <utility>
#include <vector>

// One decoded line of llm_requests.jsonl.
struct LLMRequestLogEntry
{
    uint64 seq = 0;
    std::string timestamp;
    std::string label;
    std::string model;
    std::string provider;
    uint32 durationMs = 0;
    std::string systemPrompt;
    std::string prompt;
    std::string response;
    // Caller-supplied metadata keys, in file order.
    std::vector<std::pair<std::string, std::string>> extras;
};

// Newest-last view of the tail of the request log.
//
// Reads at most LLMChatter.AddonLog.TailBytes from the end of
// the file and keeps at most LLMChatter.AddonLog.MaxEntries
// parsed lines. Results are cached process-wide and reused
// until the file's size or mtime changes; a pure append only
// costs the parse of the appended bytes.
//
// Returns false and fills `error` when the log is unreadable.
bool LoadRequestLogTail(
    std::vector<LLMRequestLogEntry>& out, std::string& error);

// Copy of the single cached entry with this seq, if present.
bool FindRequestLogEntry(
    uint64 seq, LLMRequestLogEntry& out, std::string& error);

// Path the worldserver reads, already resolved from config.
std::string GetRequestLogPath();

#endif // LLM_CHATTER_REQUEST_LOG_H
