import React, { useState, useEffect, useCallback, useRef, forwardRef, useImperativeHandle } from 'react';
import { Network } from 'vis-network/standalone';
import { DataSet } from 'vis-network/standalone';
import { ChevronDown, ChevronUp, Minimize2 } from 'lucide-react';

const Tab = forwardRef(({ isVisible = true, isCollapsed = false, onToggle }, ref) => {
  const [error, setError] = useState(null);
  const networkRef = useRef(null);
  const containerRef = useRef(null);
  const nodesDataset = useRef(new DataSet([]));
  const edgesDataset = useRef(new DataSet([]));
  const [fixedNodes] = useState(new Set(['node1', 'node2']));

  // Expose resetGraph method to parent component
  useImperativeHandle(ref, () => ({
    resetGraph: () => {
      nodesDataset.current.clear();
      edgesDataset.current.clear();
      if (networkRef.current) {
        networkRef.current.fit();
      }
    }
  }));

  const addNode = useCallback((nodeData) => {
    try {
      const { current_node: nodeId, text, text_state, parent_node: parentNodes } = nodeData;
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
        title: text_state || text || nodeId,
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

      setError(null);
    } catch (err) {
      console.error('Error adding node:', err);
      setError('Error updating graph');
    }
  }, [fixedNodes]);

  const handleToggle = () => {
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
          nodeSpacing: 150,
          treeSpacing: 200,
          blockShifting: true,
          edgeMinimization: true,
          parentCentralization: true,
          shakeTowards: 'roots'
        }
      },
      physics: {
        enabled: false,
        hierarchicalRepulsion: {
          nodeDistance: 200,
          springLength: 200,
          springConstant: 0.3,
          damping: 0.5
        },
        stabilization: {
          enabled: false
        }
      },
      nodes: {
        shape: 'box',
        margin: 10,
        widthConstraint: { minimum: 150, maximum: 250 },
        heightConstraint: { minimum: 40 },
        font: { size: 14, color: '#333', face: 'arial' },
        shadow: true,
        mass: 2
      },
      edges: {
        smooth: {
          type: 'straightCross',
          forceDirection: 'vertical',
          roundness: 0
        },
        color: '#2B7CE9',
        width: 2
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true,
        hover: true,
        navigationButtons: true,
        keyboard: true
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
      networkRef.current.fit({
        animation: {
          duration: 1000,
          easingFunction: 'easeInOutQuad'
        }
      });
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

  if (!isVisible) return null;

  return (
    <div className="flex flex-col h-full max-h-screen overflow-hidden bg-white border-l border-gray-200"> 
      <div 
        className={`flex-1 transition-all duration-300 ${
          isCollapsed ? 'h-0' : 'h-full'
        }`}
      >
        <div
          ref={containerRef}
          className="w-full h-full"
          style={{ display: isCollapsed ? 'none' : 'block' }}
        />
        {error && (
          <div className="p-4 text-red-500 text-sm">{error}</div>
        )}
      </div>
    </div>
  );
});

Tab.displayName = 'Tab';

export default Tab;