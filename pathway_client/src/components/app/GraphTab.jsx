import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Network } from 'vis-network/standalone';
import { DataSet } from 'vis-network/standalone';
import { ChevronDown, ChevronUp } from 'lucide-react';

const GraphTab = ({ isVisible = true, onToggle }) => {
  const [error, setError] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const networkRef = useRef(null);
  const containerRef = useRef(null);
  const nodesDataset = useRef(new DataSet([]));
  const edgesDataset = useRef(new DataSet([]));
  const [fixedNodes] = useState(new Set(['node1', 'node2']));

  const addNode = useCallback((nodeData) => {
    try {
      const { current_node: nodeId, text, parent_node: parentNodes } = nodeData;
      if (parentNodes === nodeId) return;
      
      // Split parent nodes if they contain $$
      const parentNodeList = parentNodes ? parentNodes.split('$$').filter(Boolean) : [];
      const parentLevel = parentNodeList.length > 0 
        ? Math.max(...parentNodeList.map(id => nodesDataset.current.get(id)?.level || 0)) 
        : -1;
      const nodeLevel = parentLevel + 1;

      // Update or create the current node
      const existingNode = nodesDataset.current.get(nodeId);
      const nodeColor = fixedNodes.has(nodeId) 
        ? { background: '#ffebcd', border: '#deb887' }
        : { background: '#D2E5FF', border: '#2B7CE9' };

      nodesDataset.current.update({
        id: nodeId,
        label: text || nodeId,
        title: text,
        level: nodeLevel,
        color: {
          ...nodeColor,
          highlight: { background: '#FFA500', border: '#FF8C00' }
        },
        font: { size: fixedNodes.has(nodeId) ? 20 : 14 },
        shape: 'box',
        margin: 10,
        shadow: true
      });

      // Handle parent nodes and create edges
      if (parentNodeList.length > 0) {
        parentNodeList.forEach(parentId => {
          parentId = parentId.trim();
          if (parentId && parentId !== nodeId) {
            // If parent node exists, update its text with current node's text
            const parentNode = nodesDataset.current.get(parentId);
            if (parentNode && !fixedNodes.has(parentId)) {
              nodesDataset.current.update({
                ...parentNode,
                label: text,
                title: text
              });
            }

            // Create edge
            edgesDataset.current.update({
              id: `${parentId}-${nodeId}`,
              from: parentId,
              to: nodeId,
              arrows: 'to',
              smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.5 },
              color: { color: '#2B7CE9', highlight: '#FFA500' }
            });
          }
        });
      }

      networkRef.current.stabilize()

      setError(null);
    } catch (err) {
      console.error('Error adding node:', err);
      setError('Error updating graph');
    }
  }, [fixedNodes]);

  const handleToggle = () => {
    setIsCollapsed(!isCollapsed);
    if (onToggle) {
      onToggle(!isCollapsed);
    }
  };

  useEffect(() => {
    if (!containerRef.current) return;

    const options = {
      layout: {
        hierarchical: {
          direction: 'UD',
          sortMethod: 'directed',
          levelSeparation: 150,
          nodeSpacing: 100,
          treeSpacing: 100,
          blockShifting: true,
          edgeMinimization: true,
          parentCentralization: true
        }
      },
      physics: {
        enabled: false,
        hierarchicalRepulsion: {
          nodeDistance: 150,
          springLength: 150
        },
        stabilization: {
          enabled: false,
          iterations: 1000,
          updateInterval: 50,
          fit: true
        }
      },
      nodes: {
        shape: 'box',
        margin: 10,
        widthConstraint: { minimum: 150, maximum: 250 },
        heightConstraint: { minimum: 40 },
        font: { size: 14, color: '#333', face: 'arial' },
        shadow: true
      },
      edges: {
        smooth: {
          type: 'cubicBezier',
          forceDirection: 'vertical',
          roundness: 0.5
        },
        color: '#2B7CE9',
        width: 2
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true,
        hover: true
      },
      autoResize: true
    };

    networkRef.current = new Network(
      containerRef.current,
      { nodes: nodesDataset.current, edges: edgesDataset.current },
      options
    );

    networkRef.current.on('stabilizationProgress', (params) => {
      console.log('Stabilization progress:', params.iterations, '/', params.total);
    });

    networkRef.current.on('stabilizationIterationsDone', () => {
      console.log('Stabilization finished');
      networkRef.current.fit();
    });

    const socket = new WebSocket('ws://127.0.0.1:6969/ws/graph');

    socket.onopen = () => {
      console.log('Connected to graph WebSocket');
      setError(null);
    };

    socket.onmessage = (event) => {
      try {
        const nodeData = JSON.parse(event.data);
        console.log('Received node:', nodeData);
        addNode(nodeData);
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
        setError('Error processing graph data');
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Failed to connect to graph service');
    };

    socket.onclose = () => {
      console.log('Disconnected from graph WebSocket');
      setError('Connection to graph service closed');
    };

    const handleResize = () => {
      if (networkRef.current) {
        networkRef.current.fit();
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
      if (networkRef.current) {
        networkRef.current.destroy();
      }
      window.removeEventListener('resize', handleResize);
    };
  }, [addNode]);

  return (
    <div className={`graph-tab ${isVisible ? 'block' : 'hidden'}`}>
      <div className={`graph-content transition-all duration-300`}>
        <div 
          ref={containerRef} 
          className="w-full h-full"
          style={{ display: isCollapsed ? 'none' : 'block' }}
        />
      </div>
      {error && (
        <div className="error-message text-red-500 text-sm p-2">
          {error}
        </div>
      )}
    </div>
  );
};

export default GraphTab;