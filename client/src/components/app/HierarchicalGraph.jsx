import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Network } from 'vis-network/standalone';
import { DataSet } from 'vis-network/standalone';

const HierarchicalGraph = ({ messageId, onClose }) => {
  const [error, setError] = useState(null);
  const networkRef = useRef(null);
  const containerRef = useRef(null);
  const nodesDataset = useRef(new DataSet([]));
  const edgesDataset = useRef(new DataSet([]));
  const wsRef = useRef(null);

  const addNode = useCallback((nodeData) => {
    try {
      const { current_node: nodeId, text, parent_node: parentNodes, message_id } = nodeData;
      
      // Only process nodes for the current message
      if (message_id && message_id !== messageId) {
        return;
      }

      if (parentNodes === nodeId) return;
      
      const parentLevel = parentNodes ? Math.max(...parentNodes.split('$$').filter(Boolean).map(id => nodesDataset.current.get(id)?.level || 0)) : -1;
      const nodeLevel = parentLevel + 1;
        
      nodesDataset.current.update({
        id: nodeId,
        label: text || nodeId,
        title: text,
        level: nodeLevel,
        color: {
          background: '#D2E5FF',
          border: '#2B7CE9',
          highlight: { background: '#FFA500', border: '#FF8C00' }
        },
        font: { size: 14 },
        shape: 'box',
        margin: 10,
        shadow: true
      });

      if (parentNodes) {
        parentNodes.split('$$').forEach(parentId => {
          parentId = parentId.trim();
          if (parentId && parentId !== nodeId) {
            if (!nodesDataset.current.get(parentId)) {
              nodesDataset.current.add({
                id: parentId,
                label: parentId,
                level: parentLevel,
                color: {
                  background: '#ffebcd',
                  border: '#deb887',
                  highlight: { background: '#FFA500', border: '#FF8C00' }
                },
                font: { size: 20 },
                shape: 'box',
                margin: 10,
                shadow: true
              });
            }
            
            const edgeId = `${parentId}-${nodeId}`;
            if (!edgesDataset.current.get(edgeId)) {
              edgesDataset.current.add({
                id: edgeId,
                from: parentId,
                to: nodeId,
                arrows: 'to',
                color: { color: '#848484' },
                smooth: {
                  type: 'cubicBezier',
                  forceDirection: 'vertical',
                  roundness: 0.4
                }
              });
            }
          }
        });
      }
    } catch (error) {
      console.error('Error adding node:', error);
      setError('Failed to add node to graph');
    }
  }, [messageId]);

  // Load historical nodes
  useEffect(() => {
    const fetchNodes = async () => {
      try {
        const response = await fetch(`http://localhost:8000/nodes/${messageId}`);
        if (!response.ok) throw new Error('Failed to fetch nodes');
        
        const nodes = await response.json();
        nodes.forEach(node => addNode(node));
      } catch (err) {
        setError('Failed to load graph data');
        console.error('Error fetching nodes:', err);
      }
    };
    fetchNodes();
  }, [messageId, addNode]);

  // Connect to WebSocket for real-time updates
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/graph/${messageId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'node') {
          addNode(data.node);
        }
      } catch (err) {
        console.error('Error processing WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      setError('WebSocket connection error');
      console.error('WebSocket error:', error);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [messageId, addNode]);

  useEffect(() => {
    if (!containerRef.current) return;

    const options = {
      layout: {
        hierarchical: {
          direction: 'UD',
          sortMethod: 'directed',
          nodeSpacing: 150,
          levelSeparation: 150
        }
      },
      nodes: {
        widthConstraint: {
          minimum: 120,
          maximum: 300
        }
      },
      edges: {
        smooth: {
          type: 'cubicBezier',
          forceDirection: 'vertical',
          roundness: 0.4
        }
      },
      physics: false
    };

    const network = new Network(
      containerRef.current,
      { nodes: nodesDataset.current, edges: edgesDataset.current },
      options
    );

    networkRef.current = network;

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
      }
    };
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="text-lg font-semibold">Process Graph</h3>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
      
      {error && (
        <div className="p-4 text-red-500">
          {error}
        </div>
      )}

      <div ref={containerRef} className="flex-grow" />
    </div>
  );
};

export default HierarchicalGraph;