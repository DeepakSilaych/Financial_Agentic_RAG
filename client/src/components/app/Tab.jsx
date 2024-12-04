import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Network } from 'vis-network/standalone';
import { DataSet } from 'vis-network/standalone';

const HierarchicalGraph = () => {
  const [error, setError] = useState(null);
  const networkRef = useRef(null);
  const containerRef = useRef(null);
  const nodesDataset = useRef(new DataSet([]));
  const edgesDataset = useRef(new DataSet([]));

  const addNode = useCallback((nodeData) => {
    try {
      const { current_node: nodeId, text, parent_node: parentNodes } = nodeData;
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
  }, []);

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

    const socket = new WebSocket('ws://192.168.156.15:8000/ws/graph');

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
    <div className="h-full flex flex-col bg-slate-200">
      <div className="border-b border-gray-200">
        {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
      </div>
      <div 
        ref={containerRef} 
        className="flex-1 w-full" 
        style={{ background: '#fafafa' }} 
      />
    </div>
  );
};

export default HierarchicalGraph;